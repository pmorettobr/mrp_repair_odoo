# Reparo Cilindros — Módulo Odoo 16

## IMPORTANTE: Nome da pasta no servidor

O módulo DEVE ser instalado com o nome de pasta exato:

    odoo_repair_mrp

Coloque em: /opt/odoo16/custom-addons/odoo_repair_mrp/

NÃO renomeie a pasta. O nome técnico do módulo é usado nos XMLIDs
internos (views, relatórios, dados iniciais).

## Dependências
- repair (nativo Odoo)
- mrp   (nativo Odoo, com Work Orders habilitado em Configurações > MRP)
- stock (nativo Odoo)

## Instalação
1. Copie a pasta odoo_repair_mrp para custom-addons
2. Reinicie o serviço Odoo
3. Ative Modo Desenvolvedor
4. Aplicativos > Atualizar Lista de Módulos
5. Busque "Reparo Cilindros" e clique Instalar
