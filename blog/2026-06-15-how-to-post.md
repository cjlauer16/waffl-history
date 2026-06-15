---
title: How to Write a WAFFL Blog Post (A Guide for Normal People)
author: cjlauer16
date: 2026-06-15
---

You're reading this, which means the blog works. Here's how you can post one yourself — no coding, no downloads, no asking Casey for help.

## What you'll need

- A GitHub account (free at [github.com](https://github.com))
- To be added as a collaborator on the repo (text Casey)
- Something to say

That's it.

## Step 1: Get to the blog folder

Go to [github.com/cjlauer16/waffl-history](https://github.com/cjlauer16/waffl-history) and click on the **blog** folder.

You'll see the existing posts listed as files. Yours will live here too.

## Step 2: Create a new file

Click **Add file → Create new file** in the top right.

Name your file like this: `2026-08-01-my-post-title.md`

The date at the front (YYYY-MM-DD) is how posts get sorted newest-first. The rest of the name is up to you — just no spaces, use dashes instead. The `.md` at the end is required.

## Step 3: Paste in the header

Every post needs a small block at the very top that looks like this:

```
---
title: I Robbed Winnie24 Blind and I'd Do It Again
author: YourLeagueName
date: 2026-08-01
---
```

Fill in your title, your league username, and today's date. Don't change anything else about the format — the dashes and colons matter.

## Step 4: Write your post

Below the header block (below the second `---`), just start typing. Write like you're texting someone. Full sentences, stream of consciousness, whatever — it'll look good.

**Want to add some formatting?** Here are the only three things worth knowing:

- Surround a word with `**double stars**` to make it **bold**
- Put a `#` before a line to make it a big heading
- Put a `-` before each line to make a bulleted list

If that sounds annoying, go to [dillinger.io](https://dillinger.io) instead — it's a free editor with actual buttons like Word. Write there, copy the result, paste it into GitHub.

## Step 5: Publish it

Scroll down to the bottom of the page. You'll see a **Commit changes** button. Click it, leave the default message, and click **Commit changes** again in the popup.

Your post will be live on the site in about 60 seconds.

## Want to save a draft first?

Add `draft: true` to your header block:

```
---
title: Still Working On This One
author: YourLeagueName
date: 2026-08-01
draft: true
---
```

It saves to GitHub (so you can come back and edit it) but won't show up on the site. When you're ready, edit the file, delete the `draft: true` line, and commit again.

## Going back to edit a post

Click on your file in the **blog** folder, then click the pencil icon (Edit) in the top right. Make your changes and commit. The site updates automatically.

---

That's the whole thing. If something breaks, text Casey.
