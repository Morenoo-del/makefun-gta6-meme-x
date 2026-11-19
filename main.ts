// Entry program for the gta6-meme-x-01 bounty.
// The entry is the X post named in POST.json; the house reads the post
// itself, so all this program has to do is hand POST.json over: copy it
// from the repository root into the output directory the house reads.
import { copyFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const POST_FILE = "POST.json";

const repoRoot = dirname(fileURLToPath(import.meta.url));
const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? "/output";

mkdirSync(outDir, { recursive: true });
copyFileSync(join(repoRoot, POST_FILE), join(outDir, POST_FILE));
