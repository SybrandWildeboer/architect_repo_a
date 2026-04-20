/**
 * BookNook Frontend JavaScript
 * Business logic in de frontend die eigenlijk server-side hoort
 */

// Live search met debounce
let searchTimeout = null;
const searchInput = document.querySelector('input[name="q"]');

if (searchInput) {
    searchInput.addEventListener('input', function(e) {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            performSearch(e.target.value);
        }, 300);
    });
}

async function performSearch(query) {
    if (query.length < 2) {
        hideSearchResults();
        return;
    }

    try {
        const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
        const data = await response.json();
        showSearchResults(data.results);
    } catch (err) {
        console.error('Search failed:', err);
    }
}

function showSearchResults(results) {
    let dropdown = document.getElementById('search-dropdown');
    if (!dropdown) {
        dropdown = document.createElement('div');
        dropdown.id = 'search-dropdown';
        dropdown.style.cssText = 'position:absolute;background:white;border:1px solid #ddd;border-radius:4px;max-height:300px;overflow-y:auto;width:100%;z-index:1000;box-shadow:0 4px 6px rgba(0,0,0,0.1);';
        searchInput.parentElement.style.position = 'relative';
        searchInput.parentElement.appendChild(dropdown);
    }

    if (results.length === 0) {
        dropdown.innerHTML = '<div style="padding:10px;color:#888;">No results found</div>';
        return;
    }

    dropdown.innerHTML = results.map(book => `
        <a href="/books/${book.id}" style="display:block;padding:10px;text-decoration:none;color:#333;border-bottom:1px solid #eee;">
            <strong>${book.title}</strong><br>
            <span style="color:#666;font-size:12px;">${book.author} - ${book.price}</span>
        </a>
    `).join('');
}

function hideSearchResults() {
    const dropdown = document.getElementById('search-dropdown');
    if (dropdown) dropdown.remove();
}

// Verberg zoekresultaten bij klik erbuiten
document.addEventListener('click', function(e) {
    if (!e.target.closest('[name="q"]') && !e.target.closest('#search-dropdown')) {
        hideSearchResults();
    }
});

// ==================== PRIJS BEREKENING IN FRONTEND ====================
// Dit hoort server-side te gebeuren, maar is ooit als "snelle fix" toegevoegd

function calculateSuggestedPrice() {
    const originalPrice = parseFloat(document.querySelector('[name="price"]')?.value || 0);
    const condition = document.querySelector('[name="condition"]')?.value;

    if (!originalPrice || !condition) return;

    // Business logic in frontend - duplicaat van server-side logica
    const multipliers = {
        'new': 1.0,
        'good': 0.75,
        'fair': 0.5,
        'poor': 0.25
    };

    const suggested = originalPrice * (multipliers[condition] || 0.5);
    const priceInput = document.querySelector('[name="price"]');

    // Toon suggestie
    let hint = document.getElementById('price-hint');
    if (!hint) {
        hint = document.createElement('small');
        hint.id = 'price-hint';
        hint.style.color = '#888';
        priceInput.parentElement.appendChild(hint);
    }
    hint.textContent = `Suggested price for ${condition} condition: €${suggested.toFixed(2)}`;
}

// Bind aan form velden
const conditionSelect = document.querySelector('[name="condition"]');
if (conditionSelect) {
    conditionSelect.addEventListener('change', calculateSuggestedPrice);
}

// ==================== RESERVERING COUNTDOWN ====================
// Countdown timer voor reserveringen - client-side berekening

function updateCountdowns() {
    document.querySelectorAll('[data-expires]').forEach(el => {
        const expires = new Date(el.dataset.expires);
        const now = new Date();
        const diff = expires - now;

        if (diff <= 0) {
            el.textContent = 'Expired';
            el.style.color = '#e74c3c';
        } else {
            const hours = Math.floor(diff / (1000 * 60 * 60));
            const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
            el.textContent = `${hours}h ${minutes}m remaining`;
        }
    });
}

setInterval(updateCountdowns, 60000);
updateCountdowns();

// ==================== LOCAL STORAGE "WISHLIST" ====================
// Hele feature in frontend JS die eigenlijk een server-side feature hoort te zijn

function getWishlist() {
    try {
        return JSON.parse(localStorage.getItem('booknook_wishlist') || '[]');
    } catch {
        return [];
    }
}

function addToWishlist(bookId, title) {
    const wishlist = getWishlist();
    if (!wishlist.find(item => item.id === bookId)) {
        wishlist.push({ id: bookId, title: title, addedAt: new Date().toISOString() });
        localStorage.setItem('booknook_wishlist', JSON.stringify(wishlist));
    }
}

function removeFromWishlist(bookId) {
    const wishlist = getWishlist().filter(item => item.id !== bookId);
    localStorage.setItem('booknook_wishlist', JSON.stringify(wishlist));
}

// ==================== FORM VALIDATIE ====================
// Client-side validatie die de server-side validatie dupliceert

document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', function(e) {
        const priceInput = form.querySelector('[name="price"]');
        if (priceInput) {
            const price = parseFloat(priceInput.value);
            if (price <= 0) {
                e.preventDefault();
                alert('Price must be positive');
                return;
            }
            if (price > 500) {
                e.preventDefault();
                alert('Price cannot exceed €500');
                return;
            }
        }

        const titleInput = form.querySelector('[name="title"]');
        if (titleInput && titleInput.value.length < 2) {
            e.preventDefault();
            alert('Title must be at least 2 characters');
            return;
        }
    });
});

console.log('BookNook v1.0 loaded');
