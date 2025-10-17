# nsj_rest_lib2

Biblioteca para permitir a distribuição de rotas dinâmicas numa API, configuradas por meio de EDLs declarativos (em formato JSON).

[ESPECIFICAÇÃO DO MODELO DE ENTIDADES](docs/especificacao.md)

## TODO
* Unificar o arquivo redis_config.py
* Usar pydantic, ou similar, para transformar a configuração das entidades, no redis, num objeto
* Rever modo de usar o InjectFactory (talvez dando ciência, ao RestLib, do padrão multibanco)
* Implementar e documentar campos join
* Implementar e documentar conjuntos
* Dar erro ao haver conflito de nomes das propriedades (por qualquer tipo de herança)
* Rotas para o inline
* inline será para composição (arquivo externo é agregação)