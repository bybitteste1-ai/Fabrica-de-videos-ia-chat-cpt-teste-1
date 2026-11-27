# Fábrica de Vídeos Própria — Starter 0.1

Projeto inicial para uma fábrica independente de vídeos. A primeira versão valida o pipeline com uma cena 3D procedural simples no Blender e exportação MP4 pelo FFmpeg.

> Esta versão ainda NÃO gera roteiros com LLM, imagens com modelos de difusão, vídeo com Wan, vozes ou lip-sync. Esses módulos serão conectados depois, sem acoplar o núcleo a um fornecedor.

## Arquitetura inicial

- `producer.py`: fila simples de jobs e orquestração.
- `blender/render_scene.py`: cria e anima uma cena 3D demonstrativa.
- `jobs/`: arquivos JSON que descrevem os vídeos.
- `outputs/`: MP4 final.
- `logs/`: registros de execução.
- `config.json`: caminhos e parâmetros padrão.

## Requisitos

- Python 3.10+
- Blender 3.6+ com suporte a execução em modo background
- FFmpeg instalado e disponível no PATH
- GPU NVIDIA opcional para acelerar renderização; a cena de teste também pode rodar em CPU, mais lentamente.

## Primeiro teste local ou no servidor

1. Instale Blender e FFmpeg no ambiente de execução.
2. Ajuste `config.json` se os executáveis não estiverem no PATH.
3. Execute:

```bash
python producer.py list
python producer.py validate jobs/demo_01.json
python producer.py run jobs/demo_01.json
```

O vídeo será salvo em `outputs/demo_01.mp4`.

## Executar em servidor RunPod

Use um Pod GPU sob demanda. Para economizar:
- não deixe o Pod ligado quando não estiver produzindo;
- configure um limite de gastos/alertas na conta;
- use volume persistente apenas se precisar manter modelos e arquivos entre sessões;
- salve os resultados importantes fora do disco efêmero antes de encerrar o Pod;
- comece com um único job de teste, não com uma fila de 20 vídeos.

O `Dockerfile` é uma base de teste, não uma imagem de produção otimizada. Verifique a versão do Blender e os drivers disponíveis no Pod escolhido.

## Próximas integrações (não ativadas nesta versão)

1. ComfyUI como worker opcional de imagem.
2. Modelo de vídeo (ex.: Wan) como worker opcional de animação.
3. Serviço/modelo local de TTS como worker de narração.
4. Geração de legendas e mixagem avançada.
5. Banco de dados e painel web para fila, status e revisão.

Cada integração deve ser testada isoladamente e ter custo medido antes de entrar no fluxo automático.
