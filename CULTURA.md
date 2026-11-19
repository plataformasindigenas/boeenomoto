# Cultura visual do Boe Eno Moto

O Boe Eno Moto usa a mesma interface das outras plataformas, mas com elementos visuais próprios. Este
arquivo diz de onde eles vêm e quem os aprovou. Os elementos de um povo **não são usados no site
de outro**.

## O padrão (`moiety`)

O círculo dividido ao meio representa as **duas metades exogâmicas Bororo, Tugarege e
Ecerae**, e a aldeia circular organizada por elas. Aparece no fundo animado da página inicial
(círculos que se expandem; os losangos saíram em 2026-11-17), na moldura das fotos, no divisor e no selo ao lado dos
títulos.

- **Onde está:** `config/templates/motifs/moiety/`; escolhido em `terradoc.yaml` (`theme`).
- **Aprovação:** aprovado (registro do coordenador, 2026-11-14).

As cores (`theme.colors`) e as fotos da página inicial (`theme.hero_images`) também fazem
parte da identidade do site; os créditos das fotos ficam junto delas.

## O alfabeto do dicionário

O dicionário agrupa e ordena as palavras por este alfabeto:

a, b, c, d, e, g, i, j, k, m, n, o, p, r, t, u, w

- É a grafia dos próprios dados: **c** para /tʃ/ (*cerae*) e **j** para /dʒ/ (*kejewu*), sem
  *č*. A coluna IPA dos dados confirma esses valores.
- **á é í ó ú** não são letras à parte: *kudógó* fica junto de *kudogo*. **kw** e **gw** também
  não têm aba própria; a ordem normal já as põe depois de *ku-* e *gu-*.
- **Fontes.** Nonato (2008, Unicamp; e "Fonética e fonologia do bororo", 2006): /tʃ/ = c,
  /dʒ/ = j, kw e gw como uma consoante. Ochoa Camargo (2005), citado por Camargos (2010, UnB,
  p. 17): o dicionário escolar adaptou a grafia da *Enciclopédia Bororo* para o computador.
  Borocereu (2025, ProfLetras/UNEMAT), professor em Meruri, escreve *Ecerae*, *poboce*,
  *pogora jiwu*. Não consegui ver as "notas sobre o alfabeto" do dicionário de Ochoa, que
  diriam se a escola trata kw, gw ou as vogais acentuadas como letras.
- Ficam fora: **l s z x ç q v f h**, que só aparecem em notas em português (*pl.*, *vrt.*) e
  empréstimos.
- **Onde está:** `alphabet` em `terradoc.yaml`. Pesquisa completa:
  `meta/domains/plataformas/research/2026-11-17-template-redesign/alphabets.md`.
- **Aprovação:** proposta de 2026-11-18, aprovada pelo coordenador sob a aprovação geral da
  comunidade ao ser incorporada. A comunidade pode pedir mudanças a qualquer momento.

## Cores da versão 2

O novo modelo usa cinco cores com papéis fixos (`theme.palette` em `terradoc.yaml`). As de
agora são as mesmas do site atual, com o nome do material de onde vêm: o fundo é a **argila
branca** e a penugem branca; o texto, o **carvão e a resina**; títulos, links e botões, o
**urucum**; faixas e destaques, o **amarelo das penas** (uma inferência nossa, não um dado da
pesquisa); o texto secundário é um cinza neutro. Todas as combinações usadas no site passam o
contraste mínimo de leitura (4,5:1). Pesquisa: `research/2026-11-17-template-redesign/bororo.md`
§0 e `palettes.md`.

## Padrões da versão 2 (rascunho)

Para o novo modelo do site (versão 2) desenhamos três elementos, em
`config/templates/v2/motifs/bororo/` (fontes e aprovação também em `pack.yaml`). Foram
desenhados como rascunho em 2026-11-18, a partir da pesquisa publicada, e registrados como
aprovados pelo coordenador sob a aprovação geral da comunidade. A comunidade pode pedir
mudanças a qualquer momento. As cores são as da paleta do site.

- **Faixa: traços de urucum.** Uma fileira reta de traços curtos e iguais, numa só cor, sob o
  cabeçalho e entre as seções. Abstrai o ritmo do traço de pintura com urucum, a pintura que
  todos os recém-nascidos recebem antes da pintura do clã (Caiuby Novaes 1986; materiais e
  pincel de buriti em Nogueira e Kiga 2020, pp. 96–97). Não é radial, não é uma pintura facial
  de clã nem a ordem de penas de um pariko. Se alguém a ler como as listras de uma pintura de
  clã, ela deve ser trocada.
- **Textura: trama de esteira.** Uma grade muito clara de tiras que passam por cima e por
  baixo, no fundo da página. Abstrai a estrutura das esteiras (*beto*) e cestos (*kodo*) do dia
  a dia, que o Museu das Culturas Dom Bosco mostra entre os objetos comuns (Calarge 2013,
  p. 219). Não copia nenhum objeto.
- **Emblema: aldeia circular.** Um anel em duas metades, ao norte e ao sul do eixo
  leste–oeste (o eixo aparece só como as duas aberturas), em volta de uma casa central
  simples, tudo numa só cor: a aldeia e as duas metades, sem cor para nenhuma
  metade ou clã (Calarge 2013, pp. 217–219; ISA, "Boe (Bororo)"). Deixamos de fora o anel de
  casas, porque oito marcas poderiam ser lidas como as posições dos clãs.

Ficam fora, de propósito: pinturas de clã, arranjos de penas, objetos funerários, a forma do
zunidor (*aije*) e figuras de espíritos. Pesquisa completa:
`meta/domains/plataformas/research/2026-11-17-template-redesign/bororo.md`.

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
