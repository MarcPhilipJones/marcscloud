#!/usr/bin/env node

import prompts from "prompts";
import {
    existsSync,
    mkdirSync,
    readFileSync,
    writeFileSync,
    cpSync,
    readdirSync,
    statSync,
} from "fs";
import { join, dirname, extname } from "path";
import { execSync } from "child_process";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const TEMPLATE_DIR = join(__dirname, "template");

// File extensions that should have tokens replaced
const TEXT_EXTENSIONS = new Set([
    ".ts",
    ".tsx",
    ".css",
    ".json",
    ".html",
    ".js",
    ".mjs",
    ".yml",
    ".yaml",
    ".md",
]);

function slugify(name) {
    return name
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/(^-|-$)/g, "");
}

function darkenHex(hex, percent) {
    const num = parseInt(hex.replace("#", ""), 16);
    const r = Math.max(
        0,
        Math.min(255, ((num >> 16) & 0xff) * (1 - percent / 100)),
    );
    const g = Math.max(
        0,
        Math.min(255, ((num >> 8) & 0xff) * (1 - percent / 100)),
    );
    const b = Math.max(0, Math.min(255, (num & 0xff) * (1 - percent / 100)));
    return `#${((1 << 24) + (Math.round(r) << 16) + (Math.round(g) << 8) + Math.round(b)).toString(16).slice(1)}`;
}

function resolveOutputPath(outputDir) {
    return join(process.cwd(), outputDir);
}

function copyWithTokens(srcDir, destDir, replacements) {
    const entries = readdirSync(srcDir);
    for (const entry of entries) {
        const srcPath = join(srcDir, entry);
        const destPath = join(destDir, entry);
        const stat = statSync(srcPath);

        if (stat.isDirectory()) {
            mkdirSync(destPath, { recursive: true });
            copyWithTokens(srcPath, destPath, replacements);
        } else {
            const ext = extname(entry).toLowerCase();
            if (TEXT_EXTENSIONS.has(ext)) {
                let content = readFileSync(srcPath, "utf-8");
                for (const [token, value] of Object.entries(replacements)) {
                    content = content.replaceAll(token, value);
                }
                writeFileSync(destPath, content, "utf-8");
            } else {
                cpSync(srcPath, destPath);
            }
        }
    }
}

async function main() {
    console.log("\n  📄 create-power-page — Power Pages SPA scaffolder\n");

    if (!existsSync(TEMPLATE_DIR)) {
        console.error(`\n  ❌ Template folder not found: ${TEMPLATE_DIR}\n`);
        process.exit(1);
    }

    const response = await prompts(
        [
            {
                type: "text",
                name: "siteName",
                message: "Site name",
                initial: "Contoso Customer Portal",
                validate: (value) =>
                    value.trim().length > 0 || "Enter a site name",
            },
            {
                type: "text",
                name: "primaryColour",
                message: "Primary colour (hex)",
                initial: "#0078d4",
                validate: (value) =>
                    /^#[0-9a-fA-F]{6}$/.test(value) ||
                    "Enter a valid hex colour (e.g. #1B5E20)",
            },
        ],
        {
            onCancel: () => {
                console.log("\n  Cancelled.\n");
                process.exit(0);
            },
        },
    );

    const siteName = response.siteName.trim();
    const primaryColour = response.primaryColour.trim();
    const projectSlug = slugify(siteName);

    const outputResponse = await prompts(
        {
            type: "text",
            name: "outputDir",
            message: "Output folder",
            initial: `./${projectSlug}`,
            validate: (value) =>
                value.trim().length > 0 || "Enter an output folder",
        },
        {
            onCancel: () => {
                console.log("\n  Cancelled.\n");
                process.exit(0);
            },
        },
    );

    const outputDir = outputResponse.outputDir.trim();
    const primaryHover = darkenHex(primaryColour, 15);
    const outputPath = resolveOutputPath(outputDir);

    if (existsSync(outputPath)) {
        console.error(`\n  ❌ Folder already exists: ${outputPath}\n`);
        process.exit(1);
    }

    const replacements = {
        "{{SITE_NAME}}": siteName,
        "{{PROJECT_SLUG}}": projectSlug,
        "{{PRIMARY_COLOUR}}": primaryColour,
        "{{PRIMARY_HOVER}}": primaryHover,
    };

    console.log(`\n  Creating ${siteName}...`);
    console.log(`  Folder:  ${outputPath}`);
    console.log(`  Colour:  ${primaryColour} (hover: ${primaryHover})\n`);

    mkdirSync(outputPath, { recursive: true });
    copyWithTokens(TEMPLATE_DIR, outputPath, replacements);

    console.log("  📦 Installing dependencies...\n");
    execSync("npm install", { cwd: outputPath, stdio: "inherit" });

    console.log(`
  ✅ ${siteName} is ready!

  Next steps:
  ───────────────────────────────────────────────────────────
  cd ${outputDir}
  npm run dev              # Local dev with mock data
  npm run deploy           # Build & deploy to Power Pages
  ───────────────────────────────────────────────────────────

  After first deploy, complete these MANUAL steps:

  1. ACTIVATE the site
     Power Pages maker portal → Inactive sites → Reactivate

  2. SET SITE VISIBILITY TO PUBLIC
     Edit site → Security → Site visibility → Public
     ⚠ Cannot be done via API — must use the UI
     ⚠ Developer environments cannot be made public

  3. WAIT FOR SSL CERTIFICATE (up to 1-2 hours)
     Expect NET::ERR_CERT_COMMON_NAME_INVALID until then

  4. ADD TABLE PERMISSION
     Edit site → Security → Table permissions → New permission
     • Name:         Contact Cases Read
     • Table:        Case (incident)
     • Access type:  Contact access
     • Relationship: Customer (customerid)
     • Read:         ✓
     • Roles:        + Add roles → Authenticated Users
     → Save

  5. RESTART THE SITE
     Edit site → ... menu → Restart site

  6. CONFIGURE PROFILE REDIRECT (optional)
     If login redirects to profile instead of homepage:
     Edit site → Advanced settings → find
     Authentication/Registration/ProfileRedirectEnabled → false

  7. REGISTER A TEST CONTACT
     Visit the site → Sign In → Register with a Dataverse
     contact's email address
`);
}

main();
