from nsj_integracao_api_client.service.cfg.base import _entidades_base

_entidades_tribo_servicos = [
    *_entidades_base,
    'ns.tipi',
    'ns.pessoasparcelamentos',
    'ns.conjuntosfichas',
    'ns.pessoasformaspagamentos',
    'servicos.tiposprojetos',
    'ns.conjuntosservicos',
    'ns.conjuntosfornecedores',
    'ns.contatos',
    'financas.titulos',
    'ns.estabelecimentosconjuntos',
    'ns.telefones',
    'ns.conjuntosunidades',
    'ns.conjuntosvendedores',
    'financas.contas',
    'financas.layoutscobrancas',
    'financas.bancos',
    'ns.cfop',
    'scritta.tabicms',
    'ns.conjuntos',
    'ns.conjuntosclientes',
    'ns.df_enderecos_retiradasentregas',
    'ns.contatosemails',
    'ns.df_fretes',
    'ns.df_fretes_volumes',
    'ns.df_linhas_impostos',
    'ns.df_pagamentos',
    'ns.df_parcelas',
    'ns.df_vendedores',
    'ns.formaspagamentos',
    'servicos.servicos',
    'financas.centroscustos',
    'ns.conjuntosprodutos',
    'financas.contasfornecedores',
    'ns.enderecos',
    'servicos.objetosservicos',
    'ns.configuracoes',
    'ns.df_docfis',
    'ns.feriados',
    'ns.pessoas',
    'ns.pessoasmunicipios',
    'financas.projetos',
]

_entidades_atendimento = [
    *_entidades_base,
    'financas.agencias',
    'financas.bancos',
    'financas.contas',
    'ns.conjuntos',
    'ns.conjuntosclientes',
    'ns.conjuntosfornecedores',
    'ns.contatos',
    'ns.contatosemails',
    'ns.enderecos',
    'ns.estabelecimentosconjuntos',
    'ns.pessoas',
    'ns.pessoasmunicipios',
    'ns.telefones',
    'servicos.objetosservicos',
]


cfg_servicos_planilha = [
    'financas.centroscustos',
    'financas.projetos',
    'financas.titulos',
    'financas.contratos',
    'financas.contasfornecedores',
    'financas.itenscontratos',
    #
    'ns.cfop',
    'ns.configuracoes',
    'ns.conjuntos',
    'ns.conjuntosclientes',
    'ns.conjuntosfichas',
    'ns.conjuntosfornecedores',
    'ns.conjuntosservicos',
    'ns.conjuntosunidades',
    'ns.conjuntosvendedores',
    'ns.df_docfis',
    'ns.estabelecimentosconjuntos',
    'ns.formaspagamentos',
    'ns.pessoas',
    'ns.df_fretes',
    'ns.df_fretes_volumes',
    'ns.df_linhas',
    'ns.df_pagamentos',
    'ns.df_vendedores',
    'ns.enderecos',
    'ns.contatos',
    'ns.telefones',
    'ns.pessoasparcelamentos',
    'ns.pessoasmunicipios',
    'ns.pessoasformaspagamentos',
    'ns.df_linhas_impostos',
    'ns.df_parcelas',
    'ns.contatosemails',
    #
    'pedidos.pessoas_empresasconcorrentes',
    'pedidos.pessoas_produtos_consumidos',
    #
    'servicos.objetosservicos',
    'servicos.servicos',
    'servicos.tiposprojetos'
]


cfg_servicos_diretorio = [
    'estoque.itens',
    'estoque.locaisdeestoques',
    'estoque.ra',
    'estoque.ra_historicos',
    'estoque.ra_itens',
    'estoque.ra_movimentos',
    'estoque.unidades',
    'estoque.veiculos',
    #
    'financas.centroscustos',
    'financas.contasfornecedores',
    'financas.contratos',
    'financas.itenscontratos',
    'financas.projetos',
    #
    'ns.cfop',
    'ns.conjuntos',
    'ns.conjuntosclientes',
    'ns.conjuntosfornecedores',
    'ns.conjuntosservicos',
    'ns.conjuntosunidades',
    'ns.conjuntosvendedores',
    'ns.contatos',
    'ns.empresas',
    'ns.enderecos',
    'ns.estabelecimentos',
    'ns.estabelecimentosconjuntos',
    'ns.gruposempresariais',
    'ns.pessoas',
    'ns.pessoasmunicipios',
    'ns.telefones',
    #
    'persona.adiantamentosavulsos',
    'persona.admissoespreliminares',
    'persona.apontamentos',
    'persona.avisosferiastrabalhadores',
    'persona.avisospreviostrabalhadores',
    #
    'servicos.objetosservicos',
    'servicos.ordensservicos',
    'servicos.ordensservicositens',
    'servicos.ordensservicosvisitas',
    'servicos.servicos',
    'servicos.servicostecnicos',
    'servicos.tiposmanutencoes',
    'servicos.tiposordensservicos',
    'servicos.tiposprojetos',
    'servicos.tiposservicos'
]

# @TODO Revisar futuramente com equipe de produto.
# a mais em relação planilha: {'ns.empresas', 'ns.estabelecimentos', 'financas.contas', 'ns.gruposempresariais', 'financas.layoutscobrancas', 'ns.tipi', 'ns.feriados', 'ns.df_enderecos_retiradasentregas', 'financas.bancos', 'scritta.tabicms', 'ns.conjuntosprodutos'}
# a menos em relação planilha: {'financas.itenscontratos', 'ns.df_linhas', 'pedidos.pessoas_empresasconcorrentes', 'pedidos.pessoas_produtos_consumidos', 'financas.contratos'}
# a mais em relação ao diretorio: {'ns.df_fretes', 'financas.titulos', 'ns.pessoasparcelamentos', 'ns.pessoasformaspagamentos', 'ns.df_fretes_volumes', 'ns.contatosemails', 'ns.conjuntosprodutos', 'financas.contas', 'ns.df_vendedores', 'financas.layoutscobrancas', 'ns.df_pagamentos', 'ns.conjuntosfichas', 'ns.df_enderecos_retiradasentregas', 'financas.bancos', 'scritta.tabicms', 'ns.df_linhas_impostos', 'ns.configuracoes', 'ns.tipi', 'ns.feriados', 'ns.formaspagamentos', 'ns.df_parcelas', 'ns.df_docfis'}
# a menos em relação ao diretório: {'servicos.ordensservicos', 'persona.admissoespreliminares', 'estoque.veiculos', 'servicos.ordensservicositens', 'estoque.locaisdeestoques', 'servicos.ordensservicosvisitas', 'persona.apontamentos', 'persona.adiantamentosavulsos', 'estoque.ra_movimentos', 'estoque.ra', 'estoque.ra_historicos', 'servicos.servicostecnicos', 'estoque.itens', 'financas.itenscontratos', 'estoque.unidades', 'servicos.tiposordensservicos', 'servicos.tiposmanutencoes', 'estoque.ra_itens', 'persona.avisospreviostrabalhadores', 'servicos.tiposservicos', 'persona.avisosferiastrabalhadores', 'financas.contratos'}

if __name__ == '__main__':
    print(len(_entidades_tribo_servicos))
    print(f" a mais em relação planilha: {set(_entidades_tribo_servicos) - set(cfg_servicos_planilha)}")
    print(f" a menos em relação planilha: {set(cfg_servicos_planilha) - set(_entidades_tribo_servicos)}")
    print(f" a mais em relação ao diretorio: {set(_entidades_tribo_servicos) - set(cfg_servicos_diretorio)}")
    print(f" a menos em relação ao diretório: {set(cfg_servicos_diretorio) - set(_entidades_tribo_servicos)}")
