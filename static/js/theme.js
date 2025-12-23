tailwind.config = {
    theme: {
        extend: {
            fontFamily: {
                sans: ['var(--font-sans)'],
            },
            colors: {
                brand: {
                    50: 'var(--color-brand-50)',
                    100: 'var(--color-brand-100)',
                    500: 'var(--color-brand-500)',
                    600: 'var(--color-brand-600)',
                    900: 'var(--color-brand-900)',
                },
                page: 'var(--color-bg-page)',
                card: 'var(--color-bg-card)',
            }
        }
    }
}
