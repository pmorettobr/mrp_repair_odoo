from odoo import models, fields, api


# Lista de componentes padrão para cilindros hidráulicos
COMPONENT_TYPES = [
    ('camisa', 'Camisa'),
    ('haste_tubular', 'Haste Tubular'),
    ('eixo_haste', 'Eixo da Haste'),
    ('cabecote_diant_sec', 'Cabeçote Diant. Secundário'),
    ('cabecote_diant_pri', 'Cabeçote Diant. Primário'),
    ('cabecote_traseiro', 'Cabeçote Traseiro'),
    ('sobreposta', 'Sobreposta'),
    ('bucha_guia', 'Bucha Guia'),
    ('tampa', 'Tampa'),
    ('conexao', 'Conexão'),
    ('ponteira', 'Ponteira'),
    ('eixo_engrenagem', 'Eixo com Engrenagem'),
    ('tirantes', 'Tirantes'),
    ('flange', 'Flange'),
    ('embolo', 'Êmbolo'),
    ('bloco_valvula', 'Bloco de Válvula'),
    ('motor_hidraulico', 'Motor Hidráulico'),
    ('carro', 'Carro'),
    ('outro', 'Outro'),
]


class RepairCylinderComponent(models.Model):
    """
    Componentes que compõem o cilindro dentro de uma OS.
    Tela 2: Cadastro de componentes e seus processos de serviço.
    """
    _name = 'repair.cylinder.component'
    _description = 'Componente do Cilindro na OS'
    _order = 'sequence, id'

    repair_id = fields.Many2one(
        comodel_name='repair.order',
        string='Ordem de Serviço',
        required=True,
        ondelete='cascade',
    )
    sequence = fields.Integer(string='Sequência', default=10)
    component_type = fields.Selection(
        selection=COMPONENT_TYPES,
        string='Tipo de Componente',
        required=True,
    )
    name = fields.Char(
        string='Nome / Descrição',
        compute='_compute_name',
        store=True,
        readonly=False,
    )
    # Processos de serviço vinculados ao componente
    process_ids = fields.One2many(
        comodel_name='repair.component.process',
        inverse_name='component_id',
        string='Processos de Serviço',
    )
    # Status geral do componente (calculado)
    component_status = fields.Selection(
        selection=[
            ('pending', 'Aguardando'),
            ('in_progress', 'Em Andamento'),
            ('done', 'Concluído'),
        ],
        string='Status',
        compute='_compute_component_status',
        store=True,
    )
    notes = fields.Text(string='Observações Gerais')

    # ── Computes ─────────────────────────────────────────────────────────────
    @api.depends('component_type')
    def _compute_name(self):
        type_dict = dict(COMPONENT_TYPES)
        for rec in self:
            if not rec.name:
                rec.name = type_dict.get(rec.component_type, '')

    @api.depends('process_ids.status')
    def _compute_component_status(self):
        for rec in self:
            statuses = rec.process_ids.mapped('status')
            if not statuses:
                rec.component_status = 'pending'
            elif all(s == 'done' for s in statuses):
                rec.component_status = 'done'
            elif any(s in ('in_progress', 'done') for s in statuses):
                rec.component_status = 'in_progress'
            else:
                rec.component_status = 'pending'

    def action_open_processes(self):
        """Abre o formulario do componente com seus processos (chamado pelo botao na tree da OS)."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Processos — %s' % self.name,
            'res_model': 'repair.cylinder.component',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.env.ref('mrp_repair_odoo.view_repair_cylinder_component_form').id,
            'target': 'new',
        }
