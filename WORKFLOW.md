Angels Academy — Workflow de Customização do Kolibri
1. Arquitetura: Por que um Theme Plugin
O Kolibri possui um sistema nativo de Theme Plugin (kolibri.core.theme_hook.ThemeHook) que permite customizar via plugin:
Página de login (background, logo, título, mostrar/ocultar branding Kolibri)
Barra superior / AppBar (cor de fundo, cor de texto, logo)
Menu lateral / SideNav (logo, título, footer com marca)
Paleta de cores (brandColors primário/secundário com 6 tons cada)
Mapeamento de tokens de cor (tokenMapping para substituir cores do tema)
Favicons e ícones do PWA
O plugin kolibri.plugins.default_theme é o tema padrão. A abordagem correta é:
Criar um novo plugin kolibri.plugins.angels_theme dentro do fork
Desabilitar default_theme e habilitar angels_theme
Todas as customizações visuais ficam encapsuladas nesse plugin
Vantagem: Quando o upstream (learningequality/kolibri) atualizar o default_theme, não haverá conflito com nossas alterações, pois estamos em um plugin separado.
2. Estratégia de Branches (Manter Sincronização com Upstream)
Branches no fork judicandus/kolibri:
develop — Sempre sincronizado 1:1 com learningequality/kolibri:develop. Nunca fazer commits diretos aqui.
angels/main — Branch principal com todas as customizações Angels. É criado a partir do develop.
angels/feature-xxx — Feature branches criados a partir de angels/main para cada tarefa específica.
Fluxo de trabalho:
upstream/develop ──► develop (sync) ──► angels/main (customizações)
                                             │
                                     angels/feature-theme-plugin
                                     angels/feature-rebranding
                                     angels/feature-dark-light-toggle
                                     angels/feature-font-opensans
Atualização com upstream:
git fetch upstream (busca novas alterações do upstream)
git checkout develop && git merge upstream/develop (atualiza develop local)
git checkout angels/main && git rebase develop (rebase das customizações sobre o upstream atualizado)
Resolver conflitos (se houver), testar, e fazer push
Remotes:
origin → github.com/judicandus/kolibri (o fork)
upstream → github.com/learningequality/kolibri (o original)
3. Categorização das Alterações
3A. Alterações via Theme Plugin (BAIXO risco de conflito)
Estas ficam 100% dentro de kolibri/plugins/angels_theme/ — um diretório novo que não existe no upstream:
Logo na AppBar (LOGO-04, ícone verde circular)
Logo no topo do SideNav (LOGO-02, "academy" horizontal verde)
Logo no footer do SideNav
Cor da AppBar: #213953
Página de login: imagem de fundo, logo Angels, título "Angels Academy"
Favicons e ícones PWA
Brand colors (primary: tons de #213953, secondary: tons de #a6c52e)
Token mapping (cores de superfície, texto, etc.)
3B. Alterações em CSS/Estilos Globais (MÉDIO risco de conflito)
Requerem tocar em arquivos do core ou de plugins existentes:
Background com gradiente radial (#0c131b → #253547 para tema escuro)
Fonte Open Sans (bundled no build)
Ajustes nos cards (border-radius 20pt, stroke #3a6388, drop shadow)
Barra de pesquisa centralizada
3C. Alterações de Texto/i18n (ALTO risco de conflito)
Tocam em dezenas de arquivos com strings traduzidas:
Substituir todas as referências a "Kolibri" por "Angels Academy"
Título da aba do browser
Mensagens de sistema e e-mails
3D. Nova Funcionalidade (toggle dark/light) (MÉDIO risco)
Requer criar um composable Vue para gerenciar estado do tema
Adicionar botão na AppBar
Alternar dinamicamente entre dois conjuntos de tokens
4. O que Pode Começar AGORA (Sem Resposta do Time)
Fase 1 — Setup (pode começar imediatamente):
Configurar remotes (upstream) e criar branch angels/main
Criar o plugin kolibri.plugins.angels_theme (esqueleto + assets PNG)
Configurar o plugin como tema padrão (desabilitar default_theme)
Fase 2 — Theme Plugin (pode começar com os PNGs que já temos):
Implementar ThemeHook com brand colors: primary (#213953), secondary (#a6c52e)
Configurar AppBar: background #213953, logo LOGO-04
Configurar SideNav: logo LOGO-02, título "Angels Academy"
Configurar SignIn: título "Angels Academy", hide Kolibri footer
Favicons temporários usando LOGO-03/04 (substituir quando SVGs chegarem)
Fase 3 — Estilos Globais:
Integrar fonte Open Sans (bundled, pesos 300/400/700 como default)
CSS do background (gradiente para tema escuro, #fbfbfb para claro)
Título da aba do browser → "Angels Academy"
Fase 4 — Rebranding textual:
Substituir referências "Kolibri" → "Angels Academy" nos textos da interface
5. O que Precisa Esperar Resposta do Time
SVGs dos logos → Substituir os PNGs no plugin (não bloqueia implementação)
Favicon final → Substituir o temporário
Imagem de login em alta resolução → Substituir no plugin
Pesos exatos da fonte → Ajustar se diferente de 300/400/700
Design do toggle dark/light → Implementar o botão
Decisão sobre ícones de navegação → Substituir se necessário
6. Ambiente de Desenvolvimento e Testes
Setup local:
git clone https://github.com/judicandus/kolibri.git
cd kolibri
pip install -r requirements/dev.txt
pnpm install
pre-commit install
export KOLIBRI_RUN_MODE=dev
kolibri manage migrate
# Terminal 1:
pnpm run python-devserver
# Terminal 2:
pnpm run watch
Teste visual via browser (MCP Floorp):
O agente de IA pode usar o MCP tool floorp para:
Abrir a instância local (http://localhost:8000)
Tirar screenshots (floorp_screenshot) para validar alterações visuais
Comparar com os mockups do PDF
Navegar entre páginas para verificar consistência
Testes automatizados:
# Python
pytest kolibri/plugins/angels_theme/test/
# Frontend
pnpm run test-jest -- --testPathPattern angels_theme
# Lint
pre-commit run --all-files
7. Infraestrutura de Deploy
Fluxo: Código → Build → Docker → Produção
Desenvolver e testar localmente
Commitar no branch angels/main
Build do Kolibri com o plugin angels_theme habilitado
Gerar imagem Docker baseada no docker/base.dockerfile
Deploy no servidor angels (substituindo a instalação atual)
Docker compose para produção (a ser criado em docker/angels/):
Container Kolibri com angels_theme habilitado
Volume persistente para KOLIBRI_HOME (dados, conteúdo)
Variáveis de ambiente para configuração
8. Checklist de Risco de Conflito por Arquivo
kolibri/plugins/angels_theme/* → NOVO, sem risco
kolibri/utils/build_config/default_plugins.py → Risco baixo (1 linha alterada)
packages/kolibri/styles/* → Risco médio (se alterarmos tokens globais)
kolibri/plugins/*/frontend/views/*.vue → Risco alto (se alterarmos diretamente)
Arquivos de i18n / strings → Risco alto (muitos, mudam frequentemente)
Princípio: Quanto menos arquivos do upstream tocamos, mais fácil é o rebase.
