from odoo import models, fields, api


class RepairOrder(models.Model):
    _inherit = 'repair.order'

    # ── Override campos nativos obrigatorios ─────────────────────────────────
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Produto (opcional)',
        required=False,
    )
    product_uom = fields.Many2one(
        comodel_name='uom.uom',
        string='Unidade de Medida',
        required=False,
    )

    # ── Tipo de Ordem ────────────────────────────────────────────────────────
    order_type = fields.Selection(
        selection=[
            ('repair', 'Reparo'),
            ('fabrication', 'Fabricacao'),
        ],
        string='Tipo de Ordem',
        default='repair',
        required=True,
        tracking=True,
    )

    # ── Identificacao do Cilindro ─────────────────────────────────────────────
    product_name = fields.Char(string='Produto / Cilindro')
    serial_code = fields.Char(string='N de Serie / TAG', copy=False, index=True)

    # ── Campos adicionais ─────────────────────────────────────────────────────
    equipment_description = fields.Char(string='Descricao Adicional')
    deadline_date = fields.Date(string='Prazo')

    # ── Vínculo MRP (Fabricação) ──────────────────────────────────────────────
    mrp_production_id = fields.Many2one(
        comodel_name='mrp.production',
        string='Ordem de Fabricacao MRP',
        readonly=True,
        copy=False,
        help='Ordem de Fabricacao MRP criada automaticamente para Fabricacao',
    )
    bom_id = fields.Many2one(
        comodel_name='mrp.bom',
        string='Lista de Materiais (BOM)',
        help='BOM usada como base para esta fabricacao',
        domain="[('type', 'in', ['normal','phantom'])]",
    )

    # ── Componentes ───────────────────────────────────────────────────────────
    cylinder_component_ids = fields.One2many(
        comodel_name='repair.cylinder.component',
        inverse_name='repair_id',
        string='Componentes',
    )

    # ── Todos os processos (view helper para aba na OS) ───────────────────────
    all_process_ids = fields.One2many(
        comodel_name='repair.component.process',
        inverse_name='repair_id',
        string='Todos os Processos',
    )

    # ── Progresso ─────────────────────────────────────────────────────────────
    total_components = fields.Integer(
        string='Total de Processos',
        compute='_compute_progress', store=True,
    )
    components_done = fields.Integer(
        string='Concluidos',
        compute='_compute_progress', store=True,
    )
    components_in_progress = fields.Integer(
        string='Em Andamento',
        compute='_compute_progress', store=True,
    )
    progress_percent = fields.Float(
        string='Progresso (%)',
        compute='_compute_progress', store=True, digits=(5, 1),
    )
    is_overdue = fields.Boolean(
        string='Atrasada',
        compute='_compute_progress', store=True,
    )

    # ── Estado da OS ─────────────────────────────────────────────────────────
    os_state = fields.Selection(
        selection=[
            ('draft', 'Rascunho'),
            ('confirmed', 'Confirmada'),
            ('in_progress', 'Em Andamento'),
            ('done', 'Concluida'),
            ('cancel', 'Cancelada'),
        ],
        string='Estado OS',
        default='draft',
        tracking=True,
    )

    # ── Computes ──────────────────────────────────────────────────────────────
    @api.depends(
        'cylinder_component_ids',
        'cylinder_component_ids.process_ids.status',
        'deadline_date',
        'os_state',
    )
    def _compute_progress(self):
        for rec in self:
            all_procs = rec.cylinder_component_ids.mapped('process_ids')
            total = len(all_procs)
            done = len(all_procs.filtered(lambda p: p.status == 'done'))
            in_prog = len(all_procs.filtered(lambda p: p.status == 'in_progress'))
            rec.total_components = total
            rec.components_done = done
            rec.components_in_progress = in_prog
            # Progresso: somente concluidos contam
            rec.progress_percent = (done / total * 100.0) if total else 0.0
            today = fields.Date.today()
            rec.is_overdue = bool(
                rec.deadline_date
                and rec.deadline_date < today
                and rec.os_state not in ('done', 'cancel')
            )

    def name_get(self):
        result = []
        for rec in self:
            name = rec.name or ''
            if rec.product_name:
                name = '%s - %s' % (name, rec.product_name)
            if rec.serial_code:
                name = '%s [%s]' % (name, rec.serial_code)
            result.append((rec.id, name))
        return result

    def _generate_serial_code(self):
        year = fields.Date.today().year
        count = self.search_count([
            ('order_type', '=', 'fabrication'),
            ('serial_code', 'like', 'CIL-%s-' % year),
        ])
        return 'CIL-%s-%03d' % (year, count + 1)

    # ── Acoes de estado ───────────────────────────────────────────────────────
    def action_confirm_os(self):
        for rec in self:
            if rec.order_type == 'fabrication' and not rec.serial_code:
                rec.serial_code = rec._generate_serial_code()
            # Cria mrp.production se fabricacao e tiver BOM
            if rec.order_type == 'fabrication' and not rec.mrp_production_id:
                rec._create_mrp_production()
        self.write({'os_state': 'confirmed'})

    def _create_mrp_production(self):
        """Cria Ordem de Fabricacao MRP vinculada a esta OS."""
        self.ensure_one()
        vals = {
            'origin': self.name,
            'product_qty': 1,
            'bom_id': self.bom_id.id if self.bom_id else False,
        }
        # Produto: usa product_id se existir, senão cria referência pelo nome
        if self.product_id:
            vals['product_id'] = self.product_id.id
            vals['product_uom_id'] = self.product_id.uom_id.id
        elif self.bom_id and self.bom_id.product_id:
            vals['product_id'] = self.bom_id.product_id.id
            vals['product_uom_id'] = self.bom_id.product_uom_id.id
        else:
            return  # Sem produto definido, nao cria MO

        production = self.env['mrp.production'].create(vals)
        self.mrp_production_id = production

    def action_start_os(self):
        self.write({'os_state': 'in_progress'})

    def action_done_os(self):
        self.write({'os_state': 'done'})

    def action_cancel_os(self):
        self.write({'os_state': 'cancel'})

    def action_open_mrp_production(self):
        """Abre a Ordem de Fabricacao MRP vinculada."""
        self.ensure_one()
        if not self.mrp_production_id:
            return
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production',
            'res_id': self.mrp_production_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
