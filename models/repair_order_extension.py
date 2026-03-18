from odoo import models, fields, api


class RepairOrder(models.Model):
    """
    Extensão do módulo Repair para suporte à gestão de OS de cilindros.
    Tela 1: Programação das Ordens de Serviço.
    """
    _inherit = 'repair.order'

    # ── Campos adicionais na OS ──────────────────────────────────────────────
    equipment_description = fields.Char(
        string='Descrição do Equipamento',
        help='Ex: Cilindro Hidráulico CH Martelo',
    )
    deadline_date = fields.Date(
        string='Prazo',
        help='Data limite para conclusão da OS',
    )
    # Componentes da OS (Tela 2)
    cylinder_component_ids = fields.One2many(
        comodel_name='repair.cylinder.component',
        inverse_name='repair_id',
        string='Componentes do Cilindro',
    )
    # Estatísticas calculadas
    total_components = fields.Integer(
        string='Total de Componentes',
        compute='_compute_progress',
        store=True,
    )
    components_done = fields.Integer(
        string='Concluídos',
        compute='_compute_progress',
        store=True,
    )
    components_in_progress = fields.Integer(
        string='Em Andamento',
        compute='_compute_progress',
        store=True,
    )
    progress_percent = fields.Float(
        string='Progresso (%)',
        compute='_compute_progress',
        store=True,
        digits=(5, 1),
    )
    is_overdue = fields.Boolean(
        string='Atrasada',
        compute='_compute_progress',
        store=True,
    )
    os_state = fields.Selection(
        selection=[
            ('draft', 'Rascunho'),
            ('confirmed', 'Confirmada'),
            ('in_progress', 'Em Andamento'),
            ('done', 'Concluída'),
            ('cancel', 'Cancelada'),
        ],
        string='Estado OS',
        default='draft',
        tracking=True,
    )

    # ── Computes ─────────────────────────────────────────────────────────────
    @api.depends(
        'cylinder_component_ids',
        'cylinder_component_ids.process_ids.status',
    )
    def _compute_progress(self):
        for rec in self:
            all_processes = rec.cylinder_component_ids.mapped('process_ids')
            total = len(all_processes)
            done = len(all_processes.filtered(lambda p: p.status == 'done'))
            in_progress = len(all_processes.filtered(lambda p: p.status == 'in_progress'))
            rec.total_components = total
            rec.components_done = done
            rec.components_in_progress = in_progress
            rec.progress_percent = (done / total * 100) if total else 0.0
            today = fields.Date.today()
            rec.is_overdue = bool(
                rec.deadline_date
                and rec.deadline_date < today
                and rec.os_state not in ('done', 'cancel')
            )

    # ── Ações de estado ───────────────────────────────────────────────────────
    def action_confirm_os(self):
        self.write({'os_state': 'confirmed'})

    def action_start_os(self):
        self.write({'os_state': 'in_progress'})

    def action_done_os(self):
        self.write({'os_state': 'done'})

    def action_cancel_os(self):
        self.write({'os_state': 'cancel'})
