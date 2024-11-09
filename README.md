# sffairmaker2 Python3 + Qt5 対応

過去のドキュメントはREADME_BKフォルダへ移動

## やりたいこと

英語対応


## Python環境

```
python3 -m venv myenv
```

今後は以下で環境に入る

```
zsh
source myenv/bin/activate
```

```
pip install -r requirements.txt
```

今後これで吐き出す

```
pip freeze > requirements.txt
```


## 起動について

`sffairmaker` フォルダをpythonの lib/site-packages に放り込んでから、

```
python -m sffairmaker.main
```

を実行してください。


