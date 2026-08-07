import { defineConfig } from 'vite';
import { resolve } from 'path';

export default defineConfig(() => {
  const entryName = process.env.ENTRY; // e.g. ENTRY=journal
  const input = entryName
    ? resolve(__dirname, `${entryName}.js`)
    : { journal: resolve(__dirname, 'journal.js'), task: resolve(__dirname, 'tasks.js'), index: resolve(__dirname, 'index.js') };

  return {
    build: {
      outDir: '../static/scripts',
      // When building a single entry (ENTRY=...), don't wipe the output dir
      // so other entry bundles (e.g. journal, task) are preserved.
      emptyOutDir: !entryName,
      rollupOptions: {
        input,
        output: {
          format: 'iife',
          entryFileNames: '[name].bundle.js',
          inlineDynamicImports: !!entryName // true for single-entry builds
        },
        manualChunks(id) {
          if (id.includes('node_modules')) {
            if (id.includes('milkdown')) return 'vendor_milkdown';
            if (id.includes('codemirror')) return 'vendor_codemirror';
            return 'vendor';
          }
        }
      }
    }
  };
});