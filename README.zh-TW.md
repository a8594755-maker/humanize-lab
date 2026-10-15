# 🧪 Humanize Lab — AI 偵測器逆向工程與心理語言學英文改寫實驗室

<p align="center">
  <b>🌐 <a href="README.md">English</a> | <a href="README.zh-TW.md">繁體中文</a> | <a href="WHITEPAPER.md">📄 逆向工程技術白皮書</a></b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/ZeroGPT_線上實測-0.0%25_AI-16a34a?style=for-the-badge" alt="ZeroGPT 0.0%">
  <img src="https://img.shields.io/badge/Turnitin_滑動視窗-12%2F12_全數過關_(%3C20%25)-2563eb?style=for-the-badge" alt="Turnitin Sliding Windows Pass">
  <img src="https://img.shields.io/badge/Desklib_DeBERTa--v3-0.48%25-0d9488?style=for-the-badge" alt="Desklib 0.48%">
  <img src="https://img.shields.io/badge/API_費用-%240_(直接用_Codex_訂閱)-7c3aed?style=for-the-badge" alt="$0 API Cost">
  <img src="https://img.shields.io/badge/拼字錯誤-0_(Word_零紅線)-dc2626?style=for-the-badge" alt="Zero Spelling Hacks">
</p>

> **為什麼真實學生寫的英文作業（特別是非英語母語留學生），丟進 ZeroGPT、Grammarly 或 Turnitin 常常被誤判為 50%+ AI？**
>
> 史丹佛大學（Stanford HAI）研究證實，商用 AI 偵測器會將 **超過 61% 的非英語母語真實作文誤判為 AI 生成**——因為教科書教的「標準三段論、高密度抽象名詞化（Nominalization）、句長均勻與零語法漂移」，在統計機率上與經過 RLHF 訓練的 GPT-4 高度重疊。
>
> **Humanize Lab** 是全球第一個開源的 **「本機多模型 + 商用滑動視窗閉環 + 心理語言學認知改寫實驗室」**。我們不靠塞隱形字元或亂改錯字（那會出現 Word 紅線或被 Turnitin 標紫字），而是結合 **本機 4 大神經網路模型**、**Turnitin 5 句重疊滑動視窗診斷**、**ZeroGPT 官方線上 API 逐句回饋** 與 **5 大心理語言學人類認知特徵**，並直接使用你既有的 **ChatGPT Plus / Pro (`Codex CLI`) 訂閱額度（\$0 API 費）** 完成改寫。

---

## 📊 逆向工程實測對照表（同一篇 450 字商業個案作業 5 種方法實測）

我們針對同一篇大學策略管理個案作業（*Ducati Business-Level Strategy*），實測了 5 種不同改寫策略在 **本機 `Fakespot (RoBERTa)`**、**`Desklib (DeBERTa-v3 / ACL RAID 學術基準)`**、**`Turnitin 6 句重疊滑動視窗`** 與 **`ZeroGPT 官方線上 API`** 的真實分數：

| 實驗階段／改寫方法 | Fakespot (`RoBERTa`) | Desklib (`DeBERTa-v3`) | Turnitin 6 句滑動視窗最高值 | ZeroGPT 線上 API | Word 拼字檢查 | 失敗或成功的關鍵原因分析 |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **0. 原始作業（標準架構）** | `88.91%` | `78.51%` | `96.40%` | `84.2%` | 正常 | `First / Second / Third` 對稱開頭與教科書標準連接詞。 |
| **1. 一般 Prompt 改寫** *(第三人稱高級商業腔)* | `14.20%` | `1.42%` | `74.10%` | ❌ **`52.9%`** *(標 9 句)* | 正常 | 使用 GPT-4 行銷腔動詞（`Catering to`、`fiercely loyal`、`winning over`），騙過本機模型卻被 ZeroGPT 與 Grammarly (`46%`) 重手標記。 |
| **2. 只看整篇平均分數** *(忽略分段滑動視窗)* | `1.02%` | `2.59%` | ❌ **`83.56%`** *(第 3 題暴衝)* | `0.0%` | 正常 | 第 1 段壓低了全文平均，但 **Turnitin 採 5–6 句重疊滑動視窗分段計分**，滑到第 3 題時單獨視窗飆到 `83.6%`。 |
| **3. 單純每幾句加拼錯字** *(`performence`, `dealship`)* | `19.55%` | `0.35%` | `61.20%` | ❌ **`38.4%`** *(標 7 句)* | ❌ 出現紅底線 | 錯字會切碎 BPE Token 讓 DeBERTa 暴跌至 `0.35%`，但 ZeroGPT 仍會抓出整句的 GPT 子句骨架，且在 Word 有紅線。 |
| **4. 🏆 Humanize Lab（心理語言學認知 + SICO 範例克隆 + 滑動視窗閉環）** | ✅ **`2.02%`** | ✅ **`0.48%`** | ✅ **`15.37%`** *(平均 `5.98%`)* | ✅ **`0.0%`** *(0 句)* | ✅ **100% 零錯字** | **全篇 12 個滑動視窗 100% 低於 Turnitin `20%` 門檻（顯示 `*%` 免標記）**、ZeroGPT `0.0%`、零拼字錯誤、100% 保留事實與數據。 |

---

## 🧠 為什麼這麼有效？五大心理語言學「真人認知特徵」

詳細理論請參閱 📄 **[逆向工程技術白皮書 (`WHITEPAPER.md`)](WHITEPAPER.md)**：

1. **去名詞化（De-Nominalization）：把「抽象名詞」還原成「具體的人做動作」**
   * ❌ **AI 習慣**：高密度抽象名詞片語（*"Faster parts availability and dealership service improve customer retention"*）。
   * ✅ **真人大腦**：用 `if / when` 具體條件動作句（***"...so if shops can get parts faster and do better repair work at dealerships, Ducati can keep current owners around and talk new buyers into trying one"***）。
2. **認知立場與語氣保留（Epistemic Hedging / 邊想邊寫感）**
   * ❌ **AI 習慣**：每句話都像百科全書一樣均質武斷。
   * ✅ **真人大腦**：自然流露推論與評估副詞（***"To me, Ducati is pretty clearly using..."***、***"...building cruisers would probably cost a ton of money"***）。
3. **語用生活化轉譯（Pragmatic Lived-Experience Translation）**
   * ❌ **AI 習慣**：照抄題目抽象字眼（`basic transportation`、`easy to repair`）。
   * ✅ **真人大腦**：轉譯成生活具體情境（***"Nobody buys a Ducati just to get to work and back"***、***"without being a headache to fix"***）。
4. **口語文法自然漂移（Spoken Grammar Drift — 100% 零拼字錯誤）**
   * 單字 100% 拼對（Word 完全無紅線），但融入美國大學生日常口語習慣：前句介紹公司 `Ducati`，後句想到公司團隊自然切換成複數 `they / their / them`；使用 `try and go after`；子句結尾自然保留介系詞（***"jumping into a market they don't know much about"***）。
5. **SICO 黃金範例克隆（Few-Shot Gold Exemplar）+ 破除三明治結尾金句**
   * 內建 TACL 2024 **SICO** 演算法的 `0.0%` 黃金對照範例，讓 `Luna (gpt-6-luna)` 第一輪就精準複製真人的長短句節奏，並嚴禁結尾口號（如 *"Deepening loyalty beats price cutting every time"*）與長破折號（`—`）。

---

## 🚀 如何在新電腦一鍵安裝與啟動（只要 2 步）

### 步驟 1：下載專案並執行首次安裝（自動下載 4 個本機模型，約 2.3 GB）
打開 **PowerShell** 執行：
```powershell
git clone https://github.com/a8594755-maker/humanize-lab.git
cd humanize-lab
powershell -ExecutionPolicy Bypass -File .\Setup.ps1
```

### 步驟 2：雙擊 `Start.bat` 啟動網頁實驗室
直接在資料夾連點兩下 **`Start.bat`**，瀏覽器就會自動打開 **`http://127.0.0.1:8391`**：
* 支援一鍵切換 **「產生改寫並比較」** 與 **「只做本機偵測」**。
* 內建 **「Turnitin 5 句重疊滑動視窗熱力診斷條」** 與 **「ZeroGPT 線上即時偵測卡片」**，每個區段是否低於 `20%` 一目了然！

---

## 🔌 雙引擎支援：可填入「自己的 LLM API 金鑰」或使用「Codex 訂閱額度」

系統左側選單提供兩種改寫引擎模式，兩者皆完整搭載 **心理語言學 5 大認知規則 + SICO 黃金範例克隆 + 雙向段落選優**：

### 模式 A：放入自己的 LLM API 金鑰（內建 7 大供應商 2026 最新模型範本）
在介面左上方「使用方式」切換為 **「自己的 LLM API」**，即可直接選擇供應商範本並填入你的 API Key：
* **OpenAI 官方**：`https://api.openai.com/v1`（預設 `gpt-6.1-sol`，亦支援 `gpt-6-astra`、`gpt-6-luna`、`gpt-5.6-sol`）
* **Anthropic Claude 官方**：`https://api.anthropic.com/v1/messages`（原生支援 Claude `x-api-key` 協定，預設 `claude-sonnet-5-5`，亦支援 `claude-opus-5-5`、`claude-fable-5-1`、`claude-haiku-5-5`）
* **Google Gemini 官方**：`https://generativelanguage.googleapis.com/v1beta/openai`（預設 `gemini-3.1-pro-preview`，亦支援 `gemini-3.8-flash`、`gemini-3.5-flash`）
* **OpenRouter**：`https://openrouter.ai/api/v1`（可自由切換 `anthropic/claude-sonnet-5.5`、`openai/gpt-6.1-sol`、`deepseek/deepseek-v4-pro` 等所有最新模型）
* **DeepSeek 官方**：`https://api.deepseek.com/v1`（預設 `deepseek-v4-pro`，亦支援 `deepseek-flash`、`deepseek-reasoner`）
* **Groq 極速推論**：`https://api.groq.com/openai/v1`（預設 `llama-4-maverick`）
* **Ollama 本機模型（100% 離線免金鑰）**：`http://127.0.0.1:11434/v1`（預設 `qwen3:14b`，免填 API Key）
* **自訂任何 OpenAI 相容端點**（API 金鑰僅保存在當前瀏覽器記憶體，絕不寫入硬碟或匯出檔案）

### 模式 B：Codex 訂閱額度模式（預設 `GPT-6 Luna + Extra High`，免 API 金鑰）
若電腦已安裝 Codex CLI 並執行過 `codex login` 登入 ChatGPT Plus / Pro 帳號，系統可在唯讀沙盒（`--sandbox read-only`）中呼叫 **`GPT-6 Luna (gpt-6-luna)`**、**`GPT-6.1 Sol (gpt-6.1-sol)`** 或 **`GPT-6 Astra (gpt-6-astra)`**，直接消耗既有訂閱額度，無須額外付費 API。
