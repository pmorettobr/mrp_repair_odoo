from odoo import models, fields, api


class RepairSubComponent(models.Model):
    """
    Catálogo de sub-componentes.
    Ex: Camisa → Êmbolo, Haste Interna, Flange, Anel de Vedação...

    Permite cadastrar os sub-componentes típicos de cada tipo de componente
    para agilizar o preenchimento das Work Orders.
    """
    _name = 'repair.sub.component'
    _description = 'Sub-componente (parte de um componente de cilindro)'
    _order = 'component_type, sequence, name'

    name = fields.Char(
        string='Nome do Sub-componente',
        required=True,
        help='Ex: Êmbolo, Haste Interna, Anel de Vedação, Flange, Pino...',
    )
    component_type = fields.Selection(
        selection=[
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
            ('todos', 'Todos os Componentes'),
            ('outro', 'Outro'),
        ],
        string='Componente Pai',
        default='todos',
        help='Filtra este sub-componente para aparecer no componente correto. '
             '"Todos" aparece em qualquer componente.',
    )
    sequence = fields.Integer(string='Sequência', default=10)
    active = fields.Boolean(default=True)
    notes = fields.Char(string='Observação')

    def name_get(self):
        result = []
        type_dict = dict(self._fields['component_type'].selection)
        for rec in self:
            if rec.component_type and rec.component_type != 'todos':
                display = f'{type_dict.get(rec.component_type)} › {rec.name}'
            else:
                display = rec.name
            result.append((rec.id, display))
        return result
