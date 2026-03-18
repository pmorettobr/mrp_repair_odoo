{
    'name': 'Repair + MRP - Gestão de OS de Cilindros',
    'version': '16.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'Integração entre Repair e MRP para gestão de Ordens de Serviço de cilindros hidráulicos',
    'description': """
        Módulo de integração entre os módulos Repair e MRP do Odoo 16.
        
        Funcionalidades:
        - Programação e gestão de Ordens de Serviço (OS) de cilindros
        - Cadastro de componentes por OS (Camisa, Haste, Êmbolo, Cabeçotes, etc.)
        - Processos de serviço por componente com máquina, setor e status
        - Apontamento de horas por processo (automático ou manual)
        - Controle de desvios e retrabalhos
        - Tela de consulta de status por OS ou por máquina
        - Geração de relatório em CSV/Excel
    """,
    'author': 'Seu Nome',
    'website': '',
    'depends': ['repair', 'mrp', 'stock', 'base'],
    'data': [
        'security/ir.model.access.csv',
        'views/repair_order_views.xml',
        'views/repair_component_views.xml',
        'views/repair_process_views.xml',
        'views/repair_status_views.xml',
        'views/repair_sub_component_views.xml',
        'views/menu.xml',
        'report/repair_os_report.xml',
        'data/repair_sub_component_data.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
