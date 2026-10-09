import { defineConfig } from 'vite';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  plugins: [tailwindcss()],
  define: { 'process.env.NODE_ENV': JSON.stringify('production') },
  build: {
    outDir: '../src/gate/static', emptyOutDir: true, cssCodeSplit: false,
    rollupOptions: {
      input: 'src/main.tsx',
      output: { entryFileNames: 'workspace.js', assetFileNames: asset => asset.names.some(name => name.endsWith('.css')) ? 'workspace.css' : '[name]-[hash][extname]' },
      onwarn(warning, warn) { if (warning.code !== 'MODULE_LEVEL_DIRECTIVE') warn(warning); },
    },
  },
});
