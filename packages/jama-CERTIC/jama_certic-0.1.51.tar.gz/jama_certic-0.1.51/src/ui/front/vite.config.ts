import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
    build: {
        minify: true,
        rollupOptions: {
            output: {
                entryFileNames: `ui/[name].js`,
                chunkFileNames: `ui/[name].js`,
                assetFileNames: `ui/[name].[ext]`
            }
        },
        chunkSizeWarningLimit:1500 //@todo: improve it...
    },
    plugins: [vue()],
})
