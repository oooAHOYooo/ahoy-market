/**
 * Utility to dynamically update the browser favicon.
 * Supports adding a 'Live' badge or a 'Playing' indicator.
 */

let originalFavicon = null;

export function setDynamicFavicon(type = 'default') {
    if (!originalFavicon) {
        originalFavicon = document.querySelector('link[rel="icon"]')?.href || '/favicon.ico';
    }

    const canvas = document.createElement('canvas');
    canvas.width = 32;
    canvas.height = 32;
    const ctx = canvas.getContext('2d');

    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.src = originalFavicon;

    img.onload = () => {
        ctx.clearRect(0, 0, 32, 32);
        ctx.drawImage(img, 0, 0, 32, 32);

        if (type === 'live' || type === 'playing') {
            // Draw a vibrant pink circle for 'Live'/'Playing'
            ctx.beginPath();
            ctx.arc(24, 8, 6, 0, 2 * Math.PI);
            ctx.fillStyle = '#ff0060';
            ctx.fill();
            
            // Subtle white border for the dot
            ctx.strokeStyle = '#ffffff';
            ctx.lineWidth = 1;
            ctx.stroke();
            
            // If playing, maybe a tiny pulse? (static for now in the icon itself)
        }

        const link = document.querySelector('link[rel="icon"]') || document.createElement('link');
        link.type = 'image/x-icon';
        link.rel = 'icon';
        link.href = canvas.toDataURL('image/x-icon');
        
        if (!document.querySelector('link[rel="icon"]')) {
            document.head.appendChild(link);
        }
    };
    
    // Fallback if image fails to load
    img.onerror = () => {
        if (type === 'default') {
            const link = document.querySelector('link[rel="icon"]');
            if (link) link.href = originalFavicon;
        }
    };
}

export function resetFavicon() {
    if (originalFavicon) {
        const link = document.querySelector('link[rel="icon"]');
        if (link) link.href = originalFavicon;
    }
}
