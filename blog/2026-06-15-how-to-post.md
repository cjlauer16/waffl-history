---
title: How to Write a WAFFL Blog Post
author: cjlauer16
date: 2026-06-15
---

Anyone in the league can write a blog post here. No coding knowledge required. This guide walks you through everything from creating an account to publishing your first post.

---

## Step 1: Create a GitHub Account

Go to [github.com](https://github.com) and click **Sign up**. All you need is an email address. GitHub is free.

Once you have an account, send your GitHub username to Casey so he can add you as a collaborator on the repo.

---

## Step 2: Accept the Collaborator Invite

After Casey adds you, GitHub will send you an email with a link to accept the invitation. Click it. If you can't find the email, log into GitHub and check [github.com/notifications](https://github.com/notifications).

Once accepted, you have write access and can post.

---

## Step 3: Go to the Blog Folder

Navigate to [github.com/cjlauer16/waffl-history](https://github.com/cjlauer16/waffl-history) and click on the **blog** folder. You'll see existing posts listed as files.

---

## Step 4: Create a New File

Click **Add file → Create new file** in the top right corner of the page.

Name your file using this format:

```
YYYY-MM-DD-your-post-title.md
```

For example: `2026-09-01-i-got-lucky-and-ill-admit-it.md`

Rules for the filename:
- Start with today's date (this controls sort order — newest shows first)
- Use dashes instead of spaces
- End with `.md`

---

## Step 5: Add the Header Block

Every post needs a small block at the very top. Copy and paste this, then fill it in:

```
---
title: Your Post Title Here
author: YourLeagueName
date: 2026-09-01
---
```

- **title** — what shows up as the post heading and in the blog list
- **author** — your league username or whatever name you want displayed
- **date** — the date of the post (YYYY-MM-DD format)

Don't change the dashes or colons. Everything in between the `---` lines is the header, and everything after the second `---` is your post body.

---

## Step 6: Write Your Post

Below the header block, just start writing. You don't need to know anything special — plain text works perfectly and will look good on the site.

---

## Step 7: Publish It

Scroll to the bottom of the page and click **Commit changes**. Leave the default message as-is and click **Commit changes** again in the popup that appears.

Your post will be live on the site in about 60 seconds.

---

## Saving a Draft

If you're not ready to publish yet, add `draft: true` to your header block:

```
---
title: Hot Take I'm Still Workshopping
author: YourLeagueName
date: 2026-09-01
draft: true
---
```

The post will be saved to GitHub and you can come back to edit it later — but it won't appear on the site. When you're ready, edit the file, remove (or change) the `draft: true` line, and commit again.

---

## Editing an Existing Post

Click on your file in the **blog** folder, then click the **pencil icon** (Edit this file) in the top right. Make your changes and click **Commit changes**. The site updates in about 60 seconds.

---

## Formatting Your Post

Plain text is totally fine and will look good. But if you want to add formatting, here's the complete reference:

### Text Styling

| What you type | What it looks like |
|---|---|
| `**bold text**` | **bold text** |
| `*italic text*` | *italic text* |
| `~~strikethrough~~` | ~~strikethrough~~ |
| `**_bold and italic_**` | ***bold and italic*** |

### Headings

Put one or more `#` signs before a line to make it a heading. More `#` signs = smaller heading.

```
# Big Heading
## Medium Heading
### Smaller Heading
```

### Lists

**Bullet list** — put a `-` or `*` before each item:
```
- First item
- Second item
- Third item
```

**Numbered list** — put `1.`, `2.`, etc. before each item:
```
1. First item
2. Second item
3. Third item
```

### Quotes

Put a `>` before a line to make it a blockquote:
```
> This is a quote or callout.
```

### Horizontal Rule (divider line)

Three dashes on their own line:
```
---
```

### Links

```
[link text](https://example.com)
```

### Code / Monospace Text

Surround inline text with backticks: `` `like this` ``

For a multi-line code block, use three backticks before and after:

```
your code or text here
```

### Line Breaks

If you want a new paragraph, leave a blank line between your text. A single line break in the editor won't create a new paragraph — you need the blank line.

---

## Don't Want to Learn All That? Use a Visual Editor

If the formatting syntax looks annoying, you can write your post in a visual editor that works like Word or Google Docs — with actual buttons for bold, italic, headings, etc. — then copy and paste the result into GitHub.

**[Dillinger.io](https://dillinger.io)** — Free, no account needed. Open it in a browser tab, write your post on the left side, see a preview on the right, then copy everything from the left side and paste it into GitHub's file editor.

**[StackEdit.io](https://stackedit.io)** — Similar to Dillinger, also free. Has a slightly more polished interface with a full toolbar.

Either one works. Write there, paste here.

---

That's everything. If something breaks or you can't figure out a step, text Casey.
