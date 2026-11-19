# Cultura visual do Boe Eno Moto

O Boe Eno Moto usa a mesma interface das outras plataformas, mas com elementos visuais próprios. Este
arquivo diz de onde eles vêm, o que fica de fora de propósito e quem os aprovou. Os elementos de
um povo **não são usados no site de outro**.

## Os elementos do site (versão 2)

O modelo do site (versão 2, no ar desde 2026-11-19 em <https://boeenomoto.terradoc.org/>)
tem quatro elementos visuais: as cores, uma faixa, uma textura de fundo e um emblema. Todos
foram desenhados por nós a partir da pesquisa publicada, como abstrações: nenhum copia um
objeto, uma pintura ou um desenho de clã. O site também funciona e parece acabado só com as
cores, e qualquer elemento pode sair a qualquer momento sem quebrar nada.

- **Onde estão:** as cores em `theme.palette` (`terradoc.yaml`); a faixa, a textura e o emblema
  em `config/templates/v2/motifs/bororo/` (desenhos em SVG, com fontes e aprovação repetidas em
  `pack.yaml`).
- **Aprovação:** desenhados em 2026-11-18 e aprovados pelo coordenador sob a aprovação geral da
  comunidade (2026-11-17); os desenhos finais foram aceitos pelo coordenador em 2026-11-19.
  A comunidade pode pedir mudanças a qualquer momento.

### Cores

Cinco cores com papéis fixos, cada uma com o nome do material de onde vem. São as mesmas do
site atual.

| Papel | Cor | Material |
|---|---|---|
| fundo | `#F4F1EA` | argila branca, penugem branca |
| texto | `#111827` | carvão e resina |
| títulos, links e botões | `#C81F2D` | urucum |
| faixas e destaques | `#D4A03A` | pena amarela (as penas amarelas estão documentadas; o tom é escolha nossa) |
| texto secundário | `#6B6F5A` | cinza neutro, sem material |

Todas as combinações usadas no site passam o contraste mínimo de leitura (4,5:1); o `terradoc
check` recusa uma paleta que não passe. O amarelo nunca é usado como cor de texto.

### Faixa: traços de urucum

Uma fileira reta de traços curtos e iguais, numa só cor (urucum), sob o cabeçalho e entre as
seções. Abstrai o ritmo do traço de pintura com urucum, a pintura que todos os recém-nascidos
recebem antes da pintura do clã (Caiuby Novaes 1986; o urucum e o pincel de buriti em Nogueira
e Kiga 2020, pp. 96–97). Não é radial, não é uma pintura facial de clã nem a ordem de penas de
um *pariko*. **Se alguém a ler como as listras de uma pintura de clã, ela deve ser trocada.**

### Textura: trama de esteira

Uma grade muito clara de tiras que passam por cima e por baixo, no fundo da página. Abstrai a
estrutura das esteiras (*beto*) e cestos (*kodo*) do dia a dia, que o Museu das Culturas Dom
Bosco mostra entre os objetos comuns (Calarge 2013, p. 219). Não copia nenhum objeto.

### Emblema: aldeia circular

Um anel em duas metades, ao norte e ao sul do eixo leste–oeste (o eixo aparece só como as duas
aberturas), em volta de uma casa central simples, tudo numa só cor. Representa a aldeia
circular e as duas metades, Tugarege e Ecerae, sem cor para nenhuma metade ou clã (Calarge
2013, pp. 217–219; Serpa, ISA). Aparece ao lado do nome do site.

- Uma primeira versão com uma linha atravessando o círculo parecia um sinal de proibido e foi
  redesenhada.
- O anel de casas ficou de fora, porque oito marcas poderiam ser lidas como as posições dos
  clãs.

### O que fica de fora, de propósito

Pinturas faciais e corporais de clã, arranjos de penas (o *pariko*, os enfeites do *kiogoaro*),
objetos funerários, objetos rituais restritos e figuras de espíritos. Na pesquisa publicada,
desenhos e enfeites pertencem a clãs e subclãs; não os usamos nem como inspiração distante.

### Fotos

A foto da página inicial mostra uma pessoa (`theme.hero_people: true`). Falta o crédito
(`theme.hero_credit`): fica como pendência, a preencher quando a equipe souber a fonte. Qualquer foto pode ser
retirada a pedido.

## O alfabeto do dicionário

O dicionário agrupa e ordena as palavras por este alfabeto:

a, b, c, d, e, g, i, j, k, m, n, o, p, r, t, u, w

- É a grafia dos próprios dados: **c** para /tʃ/ (*cerae*) e **j** para /dʒ/ (*kejewu*), sem
  *č*. A coluna IPA dos dados confirma esses valores.
- **á é í ó ú** não são letras à parte: *kudógó* fica junto de *kudogo*. **kw** e **gw** também
  não têm aba própria; a ordem normal já as põe depois de *ku-* e *gu-*. O teclado da busca
  (versão 2) tem as teclas á é í ó ú.
- **Fontes.** Nonato (2008, Unicamp, pela tabela da Wikipédia): /tʃ/ = c, /dʒ/ = j. Nonato
  (2006, "Fonética e fonologia do bororo"): kw e gw como uma consoante. Ochoa Camargo (2005), citado por Camargos (2010, UnB,
  p. 17): o dicionário escolar adaptou a grafia da *Enciclopédia Bororo* para o computador.
  Borocereu (2025, ProfLetras/UNEMAT), professor em Meruri, escreve *Ecerae*, *poboce*,
  *pogora jiwu*. Não consegui ver as "notas sobre o alfabeto" do dicionário de Ochoa, que
  diriam se a escola trata kw, gw ou as vogais acentuadas como letras.
- Ficam fora: **l s z x ç q v f h**, que só aparecem em notas em português (*pl.*, *vrt.*) e
  empréstimos.
- **Onde está:** `alphabet` e `keyboard` em `terradoc.yaml`. Pesquisa completa:
  `meta/domains/plataformas/research/2026-11-17-template-redesign/alphabets.md`.
- **Aprovação:** proposta de 2026-11-18, aprovada pelo coordenador sob a aprovação geral da
  comunidade ao ser incorporada. A comunidade pode pedir mudanças a qualquer momento.

## O modelo antigo (versão 1, até 2026-11-19)

Até 2026-11-19 o site usou o modelo antigo, com o padrão `moiety`: o círculo dividido ao
meio, que representa as **duas metades exogâmicas Bororo, Tugarege e Ecerae**, e a aldeia
circular organizada por elas. Aparecia no fundo animado da página inicial (círculos que se
expandiam; os losangos saíram em 2026-11-17), na moldura das fotos, no divisor e no selo ao lado
dos títulos.

- **Onde está:** `config/templates/motifs/moiety/`; cores em `theme.colors`, fotos em
  `theme.hero_images`. O site não usa mais esses arquivos e chaves; eles saem quando a versão 1
  sair do terradoc.
- **Aprovação:** aprovado (registro do coordenador, 2026-11-14).
- O emblema da aldeia circular o substituiu.

## Fontes

Pesquisa completa, com o que cada fonte diz e o que não foi possível consultar:
`meta/domains/plataformas/research/2026-11-17-template-redesign/bororo.md` (elementos e cores),
`alphabets.md` (alfabeto) e `palettes.md` (cores e contraste).

- Caiuby Novaes, S. (1986). *Mulheres, homens e heróis: dinâmica e permanência através do
  cotidiano da vida Bororo.* São Paulo: FFLCH/USP.
- Calarge, C. F. C. (2013). "A metáfora museográfica da organização social Bororo no Museu das
  Culturas Dom Bosco." *Tellus* 13(25): 217–229.
- Nogueira, J. F. S.; Kiga, N. L. M. (2020). "Pinturas faciais dos Boe Bororo: algumas
  considerações visuais a partir de pesquisa etnográfica, netnográfica e bibliográfica."
  *Tellus* 20(43): 87–104. DOI 10.20435/tellus.vi43.759.
- Serpa, P. "Boe (Bororo)." *Povos Indígenas no Brasil*, Instituto Socioambiental (ISA),
  <https://pib.socioambiental.org/pt/Povo:Boe_(Bororo)>.
- Nonato, R. (2006). "Fonética e fonologia do bororo." E Nonato, R. (2008), dissertação de
  mestrado, Unicamp, que não consegui abrir: vista só pela tabela da Wikipédia, "Bororo
  language".
- Camargos, L. S. (2010). Dissertação de mestrado, UnB (cita Ochoa Camargo 2005, *Pequeno
  dicionário Boróro-Português – a serviço da escola*).
- Borocereu, M. L. L. (2025). *Quando a língua faz movência: construção de um glossário na
  língua Boe.* ProfLetras/UNEMAT.

Consultados entre 2026-11-17 e 2026-11-18.

## Conhecimento restrito

Este repositório e todas as prévias são **públicos**. Conhecimento restrito (rituais,
conhecimento de clã ou de gênero, os mortos, imagens de pessoas sem autorização) **nunca entra
aqui**, nem num ramo de teste: o histórico do git guarda tudo, e apagar depois não resolve. Um
campo "oculto" não protegeria nada, porque o arquivo continuaria legível no GitHub.

- **Quem aprova:** a comunidade Bororo, por meio de quem coordena a plataforma com ela.
- **Situação em 2026-11-14:** todo o conteúdo publicado até esta data está aprovado
  (registro do coordenador, Tiago Tresoldi).
- **Retirar algo:** avise o Tiago. Ele tira o material do site na hora (todas as versões e
  prévias) e remove-o do repositório; a remoção do histórico é pedida ao suporte do GitHub.
  Até lá, o material continua acessível a quem tiver o endereço exato do commit.
