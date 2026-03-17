from odoo import models, fields, api
from odoo.exceptions import ValidationError

SERVICE_TYPES = [
    ('desplacar', 'Desplacar'),
    ('brunimento', 'Brunimento'),
    ('cromo', 'Cromo / Cromagem'),
    ('polimento', 'Polimento'),
    ('usinagem_prep', 'Usinagem de Preparação'),
    ('usinagem_final', 'Usinagem Final'),
    ('usinagem', 'Usinagem'),
    ('revestimento', 'Revestimento'),
    ('ajuste', 'Ajuste'),
    ('inspecao', 'Inspeção / CQ'),
    ('solda', 'Solda'),
    ('pintura', 'Pintura'),
    ('montagem', 'Montagem'),
    ('desmontagem', 'Desmontagem'),
    ('servico_externo', 'Serviço Externo'),
    ('outro', 'Outro'),
]

STATUS_TYPES = [
    ('waiting', 'Aguardando'),
    ('in_progress', 'Em Andamento'),
    ('done', 'Concluído'),
    ('deviation', 'Com Desvio'),
]


class RepairComponentProcess(models.Model):
    """
    Processos de serviço de cada componente de cilindro.

    Identificação completa de uma operação:
        Componente (ex: Camisa) >> Sub-componente (ex: Embolo) >> Servico (ex: Polimento)

    Exibida de forma concatenada no campo `operation_label`:
        "Camisa - Embolo - Polimento"
    """
    _name = 'repair.component.process'
    _description = 'Processo de Servico do Componente'
    _order = 'sequence, id'

    component_id = fields.Many2one(
        comodel_name='repair.cylinder.component',
        string='Componente',
        required=True,
        ondelete='cascade',
    )
    repair_id = fields.Many2one(
        comodel_name='repair.order',
        string='Ordem de Servico',
        related='component_id.repair_id',
        store=True,
    )
    sequence = fields.Integer(string='Sequencia', default=10)

    # ── SUB-COMPONENTE ───────────────────────────────────────────────────────
    sub_component_id = fields.Many2one(
        comodel_name='repair.sub.component',
        string='Sub-componente',
        help='Parte especifica do componente sendo trabalhada.\n'
             'Ex: Camisa > Embolo, Camisa > Anel de Vedacao, Haste > Pino...',
        domain="[('component_type', 'in', [component_type_filter, 'todos'])]",
    )
    sub_component_name = fields.Char(
        string='Sub-comp. (livre)',
        help='Preencha aqui se o sub-componente nao estiver cadastrado na lista.',
    )
    component_type_filter = fields.Char(
        related='component_id.component_type',
        store=False,
        readonly=True,
    )

    # ── SERVICO / OPERACAO ───────────────────────────────────────────────────
    service_type = fields.Selection(
        selection=SERVICE_TYPES,
        string='Processo (Servico)',
        required=True,
    )
    service_name = fields.Char(
        string='Descricao do Servico',
        compute='_compute_service_name',
        store=True,
        readonly=False,
    )

    # ── LABEL CONCATENADO ────────────────────────────────────────────────────
    operation_label = fields.Char(
        string='Operacao',
        compute='_compute_operation_label',
        store=True,
        help='Identificacao completa: Componente - Sub-componente - Servico',
    )

    # ── MAQUINA / SETOR ──────────────────────────────────────────────────────
    workcenter_id = fields.Many2one(
        comodel_name='mrp.workcenter',
        string='Maquina / Centro de Trabalho',
    )
    machine_code = fields.Char(
        string='Codigo da Maquina',
        related='workcenter_id.code',
        store=True,
        readonly=True,
    )
    department = fields.Char(string='Setor')

    # ── STATUS E TEMPO ───────────────────────────────────────────────────────
    status = fields.Selection(
        selection=STATUS_TYPES,
        string='Status',
        default='waiting',
        required=True,
        tracking=True,
    )
    time_start = fields.Datetime(string='Inicio')
    time_end = fields.Datetime(string='Fim')
    duration_hours = fields.Float(
        string='Duracao (h)',
        compute='_compute_duration',
        store=True,
        digits=(5, 2),
    )

    # ── DESVIOS ──────────────────────────────────────────────────────────────
    has_deviation = fields.Boolean(string='Houve Desvio?')
    deviation_description = fields.Text(string='Descricao do Desvio')
    notes = fields.Text(string='Observacao')

    # ── COMPUTES ─────────────────────────────────────────────────────────────

    @api.depends('service_type')
    def _compute_service_name(self):
        type_dict = dict(SERVICE_TYPES)
        for rec in self:
            if not rec.service_name:
                rec.service_name = type_dict.get(rec.service_type, '')

    @api.depends(
        'component_id.name',
        'sub_component_id.name',
        'sub_component_name',
        'service_name',
        'service_type',
    )
    def _compute_operation_label(self):
        service_dict = dict(SERVICE_TYPES)
        for rec in self:
            parts = []
            if rec.component_id:
                parts.append(rec.component_id.name or '')
            if rec.sub_component_id:
                parts.append(rec.sub_component_id.name)
            elif rec.sub_component_name:
                parts.append(rec.sub_component_name)
            service = rec.service_name or service_dict.get(rec.service_type, '')
            if service:
                parts.append(service)
            rec.operation_label = ' - '.join(filter(None, parts))

    @api.depends('time_start', 'time_end')
    def _compute_duration(self):
        for rec in self:
            if rec.time_start and rec.time_end:
                delta = rec.time_end - rec.time_start
                rec.duration_hours = delta.total_seconds() / 3600.0
            else:
                rec.duration_hours = 0.0

    @api.onchange('sub_component_id')
    def _onchange_sub_component_id(self):
        if self.sub_component_id:
            self.sub_component_name = False

    def action_start(self):
        for rec in self:
            if rec.status not in ('waiting', 'deviation'):
                raise ValidationError(
                    'O processo "%s" nao pode ser iniciado com status "%s".' % (
                        rec.operation_label,
                        dict(STATUS_TYPES).get(rec.status),
                    )
                )
            rec.write({'status': 'in_progress', 'time_start': fields.Datetime.now()})

    def action_done(self):
        for rec in self:
            vals = {'status': 'done', 'time_end': fields.Datetime.now()}
            if not rec.time_start:
                vals['time_start'] = fields.Datetime.now()
            rec.write(vals)

    def action_set_deviation(self):
        self.write({'status': 'deviation', 'has_deviation': True})

    def action_reset_waiting(self):
        self.write({'status': 'waiting'})

    @api.constrains('time_start', 'time_end')
    def _check_times(self):
        for rec in self:
            if rec.time_start and rec.time_end:
                if rec.time_end < rec.time_start:
                    raise ValidationError('A hora de Fim nao pode ser anterior ao Inicio.')
