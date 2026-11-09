# STAT 236 — Final Projects

Explore the final projects from all 12 groups. Each top-level group folder contains its project page and any supporting files.

## Project directory

Click a project title to open its main HTML file. On the published GitHub Pages site, these links open the rendered, interactive projects. In GitHub's repository view, they open the HTML source.

| Group folder | Main project page |
| --- | --- |
| `ANNIE` | [Who Should We Test?](./ANNIE/Annie_Zidan_Yinpeng_Aniket_Who%20Should%20We%20Test_%20%E2%80%94%20STAT%20236%20Research%20Project.html) |
| `BRUCE_TANG` | [Ownership Communities](./BRUCE_TANG/ownership_communities.html) |
| `CHENXI_GE` | [How Certain Is the Chatbot Arena Leaderboard?](./CHENXI_GE/STAT236_Final_Project.html) |
| `CINDY_SUN` | [Market Regime Clustering](./CINDY_SUN/index.html) |
| `ELVIN_LO` | [When Does Contiguity Help Watermark Detection?](./ELVIN_LO/When%20Does%20Contiguity%20Help%20Watermark%20Detection_.html) |
| `ERIC_TONG` | [Compression and the v4 Dip](./ERIC_TONG/Eric_Tong.html) |
| `FAYE_FANG` | [Do Social Circles Share Music Taste?](./FAYE_FANG/html/index.html) |
| `HIMAL` | [Text Analysis of Local School Board Meetings](./HIMAL/Text%20Analysis%20of%20Local%20School%20Board%20Meetings.html) |
| `IRENE_TAN` | [Fragmenting Capital](./IRENE_TAN/STAT%20236%20Course%20Project_Timeline%201_Group%203_Irene%20Tan%2C%20Liangzong%20Ma%2C%20Tianruo%20Zhang/Webpage.html) |
| `KRYSTAL_QIU` | [How Sparse Are Useful Transformer Representations?](./KRYSTAL_QIU/How%20Sparse%20Are%20Useful%20Transformer%20Representations_%20%28STAT%20236%20project%29.html) |
| `MARGARET_LEE` | [Congress Is Non-binary](./MARGARET_LEE/congress_is_non-binary.html) |
| `TONG_ZHOU` | [From Purchases to Communities](./TONG_ZHOU/Tong%20Zhou_Sia%20Xie_Yilin%20Jiang_Mingjiao%20Diao_From%20Purchases%20to%20Communities%20_%20STAT%20236.html) |

Faye's main page is `FAYE_FANG/html/index.html`. Irene's main page is `Webpage.html` inside the nested course-project folder. The ZIP archives in Irene's folder are supporting downloads, not additional group entries.

## View locally

From this folder, start a local web server:

```sh
python3 -m http.server 8000
```

Open <http://localhost:8000/>, then navigate to a group folder and its HTML file. Press **Ctrl+C** in Terminal to stop the server. You can also open the HTML files directly in a browser, although some browser features work better through a local server.

Keep each HTML file together with its supporting folders. Some projects also use external libraries, fonts, reports, or links to the group's original website and need an internet connection.

## Connect this folder to GitHub

1. Sign in at [GitHub](https://github.com/new) and create an empty repository named `STAT236-YEAR2026`. Choose **Public** if you want to use GitHub Pages with GitHub Free. Leave the options to add a README, `.gitignore`, and license unchecked; this folder already has its own README and `.gitignore`.
2. Open Terminal and run:

   ```sh
   cd /Users/paopao/Desktop/STAT236
   git init -b main
   git add .
   git commit -m "Add STAT 236 final projects and project directory"
   ```

   If Git asks for your identity, run the following with your own details, then retry the commit:

   ```sh
   git config user.name "Your Name"
   git config user.email "YOUR_GITHUB_EMAIL"
   ```

3. Connect to the collection repository, then run:

   ```sh
   git remote add origin https://github.com/ZhengTracyKe/STAT236-YEAR2026.git
   git push -u origin main
   ```

   Authenticate when prompted. For HTTPS authentication, use a personal access token rather than your GitHub account password. Alternatively, if GitHub CLI is installed, run `gh auth login` and follow the browser sign-in prompts before pushing.

## Publish the interactive projects with GitHub Pages

1. Open your repository on GitHub and select **Settings → Pages**.
2. Under **Build and deployment**, choose **Deploy from a branch**.
3. Select **main** and **/ (root)**, then click **Save**.
4. Once deployment finishes, use **Visit site** on the Pages settings screen. For a repository named `STAT236-YEAR2026`, the address is normally `https://ZhengTracyKe.github.io/STAT236-YEAR2026/`.

GitHub Pages supports this root `README.md` as the site's entry page. Its relative project links will point to the HTML files on the same site. Allow up to 10 minutes for publication.

## Update the collection

After editing files, publish the changes with:

```sh
git add .
git commit -m "Update final projects"
git push
```

When adding a new group or renaming its main HTML file, update the project directory above. Links are relative to this folder, so they do not require a GitHub username or repository name.

Setup references: [Add local files to GitHub](https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github), [Create a GitHub Pages site](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site), and [Configure its publishing source](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site).
