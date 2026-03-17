from odoo import models, fields, api
import base64
import csv
import io


class RepairExportWizard(models.TransientModel):
    _name = 'repair.export.wizard'
    _description = 'Exportar Relatorio de OS / Maquina'

    export_type = fields.Selection(
        selection=[('os', 'Por Ordem de Servico'), ('machine', 'Por Maquina')],
        string='Tipo de Relatorio', default='os', required=True,
    )
    repair_id = fields.Many2one('repair.order', string='Ordem de Servico')
    workcenter_id = fields.Many2one('mrp.workcenter', string='Maquina')
    status_filter = fields.Selection(
        selection=[
            ('all', 'Todos os Status'),
            ('waiting', 'Aguardando'),
            ('in_progress', 'Em Andamento'),
            ('done', 'Concluidos'),
            ('deviation', 'Com Desvio'),
        ],
        string='Filtrar por Status', default='all',
    )

    def action_export_csv(self):
        domain = []
        filename = 'relatorio_os'

        if self.export_type == 'os' and self.repair_id:
            domain.append(('repair_id', '=', self.repair_id.id))
            filename = 'OS_%s' % self.repair_id.name
        elif self.export_type == 'machine' and self.workcenter_id:
            domain.append(('workcenter_id', '=', self.workcenter_id.id))
            filename = 'Maquina_%s' % self.workcenter_id.name

        if self.status_filter != 'all':
            domain.append(('status', '=', self.status_filter))

        processes = self.env['repair.component.process'].search(domain)

        output = io.StringIO()
        writer = csv.writer(output, delimiter=';')

        # Cabecalho com 3 colunas separadas de identificacao
        writer.writerow([
            'OS', 'Cliente', 'Equipamento',
            'Componente',          # Coluna 1
            'Sub-componente',      # Coluna 2
            'Servico',             # Coluna 3
            'Maquina', 'Cod. Maquina', 'Setor',
            'Status', 'Inicio', 'Fim', 'Duracao (h)',
            'Desvio', 'Descricao Desvio', 'Observacao',
        ])

        for p in processes:
            # Sub-componente: lista tem prioridade sobre campo livre
            sub = ''
            if p.sub_component_id:
                sub = p.sub_component_id.name
            elif p.sub_component_name:
                sub = p.sub_component_name

            writer.writerow([
                p.repair_id.name,
                p.repair_id.partner_id.name,
                p.repair_id.equipment_description or '',
                p.component_id.name,                          # Coluna 1
                sub,                                          # Coluna 2
                p.service_name,                               # Coluna 3
                p.workcenter_id.name if p.workcenter_id else '',
                p.machine_code or '',
                p.department or '',
                dict(p._fields['status'].selection).get(p.status),
                p.time_start.strftime('%d/%m/%Y %H:%M') if p.time_start else '',
                p.time_end.strftime('%d/%m/%Y %H:%M') if p.time_end else '',
                '%.2f' % p.duration_hours if p.duration_hours else '0,00',
                'Sim' if p.has_deviation else 'Nao',
                p.deviation_description or '',
                p.notes or '',
            ])

        csv_content = output.getvalue().encode('utf-8-sig')  # BOM para Excel PT-BR

        attachment = self.env['ir.attachment'].create({
            'name': '%s.csv' % filename,
            'type': 'binary',
            'datas': base64.b64encode(csv_content),
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'text/csv',
        })
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%d?download=true' % attachment.id,
            'target': 'new',
        }
