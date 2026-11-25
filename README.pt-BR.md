# ML Split Audit

[English](README.md) · [Como contribuir](CONTRIBUTING.md)

Detecte arquivos idênticos e grupos repetidos entre treino, validação e teste antes de interpretar o desempenho de um modelo. Use Python 3.11 ou posterior.

```sh
python3 -m ml_split_audit examples/dataset.csv
```

O manifesto em CSV usa `path,split` e pode trazer `group_id`. Use caminhos relativos à pasta do manifesto e as divisões `train`, `validation` e `test`. Um grupo pode identificar o documento, a sessão de gravação ou a coleta que deu origem a várias amostras. O relatório mostra as linhas e as divisões envolvidas sem exibir arquivos, hashes ou identificadores de grupo.

O exemplo retorna `1` e mostra dois achados. O retorno `0` indica que as verificações não encontraram sobreposição, e `2` indica entrada inválida. Arquivos parecidos com bytes diferentes exigem outras verificações.
