# Bridge Dealer

此為 HSNUBC-37th 開發的橋牌自動發牌程式，主要用於練習叫牌，原程式由 Jonah 撰寫。

在 GitHub Pages 或本機開啟 `index.html` 即可互動發牌。無 JavaScript 的瀏覽器可直接開啟 `boards/index.html` 選擇預先產生的牌局。

三人玩法中，四家各持 13 張。北家固定為夢家，公開 1 張，另外 12 張分給東、南、西各查看 4 張。查看的 4 張夢家牌 HCP 最高者首叫，同分時依東、南、西的順序決定。

## 下載與更新

- `bridgeDealer.tar.gz` 是目前網站的快照。解壓後開啟 `index.html`，即可使用互動版或進入靜態牌庫。
- `boards.zip` 與 `boards.tar.gz` 包含靜態牌庫及產生器。解壓後開啟 `boards/index.html`。

修改首頁、靜態牌庫或產生器後，執行以下指令更新三個下載包，並一併提交。GitHub Actions 會在推送與 pull request 時核對每個封存檔的內容。

```sh
python3 package_site.py
python3 package_site.py --check
```

若要重新發整批靜態牌局，可執行以下指令。加上 `--seed 整數` 可以重現同一批牌。

```sh
python3 staticDealer.py --out boards --random-count 200 --with-duplicate --with-three-player
python3 package_site.py
```

## 歷史版本

Discord Bot 已退役，原始程式保存在 `heritage/main.py` 和 `heritage/bridge.py`。`heritage/` 也收錄先前版本的網頁與下載包。
