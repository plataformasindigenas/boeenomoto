# Como editar o Boe Eno Moto

Este repositório **é** o site <https://boeenomoto.terradoc.org/>. Quem edita aqui não precisa
instalar nada nem publicar nada à mão: cada alteração salva no GitHub é verificada e, se estiver
tudo certo, aparece no site em poucos minutos.

## Onde fica cada coisa

| O que | Arquivo |
|---|---|
| Dicionário | `data/dictionary.tsv` (tabela separada por tabulações) |
| Enciclopédia | `data/encyclopedia/*.md` (um arquivo por verbete) |
| Fauna | `data/fauna.yaml` |
| Etnobotânica | `data/ethnobotany.yaml` |
| Vídeos | `data/videos.yaml` |
| Bibliografia | `data/bororo.bib` |
| Imagens e áudios | `static/` (copiados para o site como estão) |
| Textos da interface (menus, títulos) | `locales/pt.yaml`, `locales/en.yaml` |

## Duas maneiras de editar

**No navegador.** Abra o arquivo no GitHub, clique no lápis (✏️ *Edit this file*), faça a
alteração e clique em *Commit changes…*. Escreva em uma linha o que mudou.

**Na sua cópia local** (git): edite, faça `git commit` e `git push`. Para ver o site no seu
computador antes de enviar: `bash scripts/build.sh` e abra `docs/index.html`.

## O site oficial e as prévias

- O ramo **`master`** é o site oficial: <https://boeenomoto.terradoc.org/>.
- **Qualquer outro ramo** vira uma **prévia**, um site completo só para conferir, em
  `https://previews.terradoc.org/boeenomoto/<nome-do-ramo>/`.
  A lista de prévias está em <https://previews.terradoc.org/boeenomoto/>.

Para testar algo sem mexer no site oficial: ao salvar no navegador, escolha *Create a new
branch* (o GitHub sugere um nome como `FFGerardi-patch-1`; pode manter). Alguns minutos depois a
prévia aparece. Quando estiver bom, abra um *pull request* e junte ao `master`; depois apague o
ramo, e a prévia some sozinha.

O nome da prévia é o nome do ramo em minúsculas, com qualquer caractere que não seja letra, número
ou hífen trocado por `-` (`Fauna_Nova` → `fauna-nova`). Dois ramos que dariam o mesmo nome não são
publicados: renomeie um deles.

## Quanto tempo leva

Cerca de 2 a 3 minutos para a verificação e a construção, mais até 2 minutos para o servidor
buscar a nova versão. A aba **Actions** do repositório mostra o andamento.

## Quando algo dá errado

Nada quebrado chega ao site: **o site continua com a última versão boa.** Você fica sabendo assim:

1. o commit ganha um ❌ vermelho; ao abrir, cada problema aparece **ao lado da linha** do arquivo;
2. abre-se uma *issue* chamada **"Publicação falhou: &lt;ramo&gt;"**, que explica cada problema (em
   português e inglês) e menciona quem enviou a alteração, e o GitHub manda um e-mail.

Corrija e salve de novo. Quando a próxima verificação passar, a *issue* se fecha sozinha.

Erros comuns: um `id` repetido no dicionário, uma coluna a mais ou a menos numa linha da tabela,
uma imagem citada que não existe em `static/`, um vídeo sem o campo `consent`.

**Apagar muito conteúdo de uma vez é bloqueado** (mais de 20 registros ou 10 % de uma seção, ou
muitos arquivos). Se for de propósito, escreva numa linha da mensagem do commit:
`confirma-reducao`.

## Como desfazer

- **Na cópia local:** `git revert <commit>` e `git push`.
- **No navegador:** abra o arquivo, clique em *History*, abra a versão anterior, copie o conteúdo
  e salve-o por cima da versão atual.
- **Urgente** (algo que não pode ficar no ar nem mais um minuto): fale com o Tiago, que pode voltar
  o site para uma versão anterior na hora.

## Consentimento: leia antes de enviar qualquer gravação, foto ou texto

Este repositório é **público**. Tudo o que for enviado a **qualquer ramo**, inclusive uma prévia,
fica visível para todos, e **apagar depois não resolve**: o histórico do git guarda tudo, e só o
suporte do GitHub consegue remover de verdade.

- **Nunca envie material cujo consentimento ainda está pendente.** Guarde-o fora do repositório até
  a comunidade aprovar.
- Cada vídeo e cada gravação precisa do campo `consent`:
  - `consent: approved`: a comunidade aprovou que este site publique ou hospede o material;
  - `consent: external`: vídeo público de outra pessoa que só incorporamos (por exemplo, do YouTube).

  Sem um desses dois valores, a publicação é bloqueada.
- Se algo foi enviado por engano, avise o Tiago **imediatamente**: ele tira o material do site na
  hora, e a remoção do histórico é pedida ao GitHub.

Os padrões visuais do site e as regras sobre conhecimento restrito estão em
[`CULTURA.md`](CULTURA.md).

## Dúvidas

Pergunte ao Tiago. Detalhes técnicos de como a publicação funciona:
<https://github.com/plataformasindigenas/terradoc/blob/master/docs/publishing.md>.
