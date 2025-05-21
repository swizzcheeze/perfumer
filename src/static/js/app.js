// Main Application JavaScript
const app = Vue.createApp({
    data() {
        return {
            // --- Dark Mode State ---
            isDarkMode: false,

            // --- Navigation & View Management ---
            currentMainView: 'ingredients', 
            
            // --- Ingredients Data & State ---
            ingredients: [],
            ingredientSearch: '', 
            ingredientCategoryFilter: '', 
            ingredientPagination: { page: 1, per_page: 10, total_pages: 1, total_items: 0 },
            currentIngredient: { category_ids: [] },    
            viewedIngredient: null,              
            selectedIngredientIds: [],              
            sortKey: 'name',                        
            sortAsc: true,                          
            editingIngredientId: null, 
            
            searchDebounceTimer: null,
            resizeDebounceTimer: null,
            estimatedRowHeight: 58, 
            minPerPage: 5,        
            initialPerPageAdjustDone: false, 

            newIngredientPanel: { name: '', amount: null, unit: 'g', category_ids: [], notes: '' },
            
            // --- Categories Data & State ---
            categories: [], 
            showAddCategoryForm: false, 
            newCategory: { name: '', description: '', parent_id: null }, 
            editingCategoryId: null, 
            categoryEditBuffer: { id: null, name: '', description: '', parent_id: null }, 
            batchCategoriesToApply: [], 
            
            // --- Formulas Data & State ---
            formulas: [],
            formulaSearch: '',
            formulaPagination: { page: 1, per_page: 10, total_pages: 1, total_items: 0 },
            currentFormula: { name: '', description: '', creator: '', version: '1.0', is_draft: true, notes: '', ingredients: [] },
            viewedFormula: null, 
            formulaModalMode: 'add', 
            formulaModalInstance: null, 
            viewFormulaModalInstance: null, 
            allIngredientsForSelection: [], 
            formulaIngredientUnits: ['g', 'mL', 'drops', 'uL', 'oz', 'lb', 'kg', 'fl oz', 'pt', 'qt', 'gal', '%', 'parts', 'units', 'ea'],

            // --- Import/Export Data & State ---
            importFile: null, importFileObject: null, rawFileContent: null,
            importAnalysis: { format: '', structure: '', fields: [], item_count: 0, sample_data: [], mapping_suggestion: {}, main_array_key: null, data_path: '', message: '' },
            importMapping: {}, importType: 'ingredients', importStatus: '', importSuccess: false, importErrors: [],
            isAnalyzingFile: false, fileAnalyzedSuccessfully: false, categoryWarnings: [],
            
            // --- AI Integration Data & State ---
            // These will store dynamically fetched models or fallbacks
            openrouterModels: [], 
            geminiModels: [],          
            claudeModels: [], 
            
            // Default system prompts (can be overridden by user or fetched)
            openrouterSystemPrompt: "You are an expert perfumer...", 
            geminiSystemPrompt: "You are a perfumery assistant...", 
            claudeSystemPrompt: "You are Claude, an AI assistant...", 
            
            apiKeys: { 
                openrouter: '',
                gemini: '',
                claude: ''
            },
            showApiKeys: { 
                openrouter: false,
                gemini: false,
                claude: false
            },
            apiSettingsModalInstance: null,
            apiKeySaveStatus: '', 
            
            savedPrompts: [], newPromptName: '', currentPromptService: '', 
            showContextualAIPanel: false, contextualAIItem: null, 
            
            aiFormulaUserDescription: '',
            aiSelectedService: 'gemini', 
            aiSelectedModel: '', 
            aiTargetTotalQuantity: '', // User input for desired total formula quantity
            aiGeneratedFormulaIngredients: [], 
            isLoadingAIFormula: false,
            aiFormulaError: '',
            serviceToFetchModelsFor: 'openrouter', // Default for the manual fetch button
            modelFetchStatus: '', 
            
            // --- General UI State ---
            lastUpdatedTimestamp: new Date().toISOString(),
            resizing: false, resizingColumn: null, startX: 0, startWidth: 0
        };
    }, 
    computed: {
        pageNumbers() { 
            const pages = []; 
            const maxPagesToShow = 5; 
            const currentPage = this.ingredientPagination.page; 
            const totalPages = this.ingredientPagination.total_pages;
            if (totalPages <= 1) return [];
            if (totalPages <= maxPagesToShow) { 
                for (let i = 1; i <= totalPages; i++) pages.push(i); 
            } else { 
                let startPage = Math.max(1, currentPage - Math.floor(maxPagesToShow / 2)); 
                let endPage = Math.min(totalPages, startPage + maxPagesToShow - 1); 
                if (endPage - startPage + 1 < maxPagesToShow) {
                    startPage = Math.max(1, endPage - maxPagesToShow + 1);
                }
                for (let i = startPage; i <= endPage; i++) pages.push(i); 
            }
            return pages;
        },
        formulaPageNumbers() {
            const pages = [];
            const maxPagesToShow = 5;
            const currentPage = this.formulaPagination.page;
            const totalPages = this.formulaPagination.total_pages;
            if (totalPages <= 1) return [];
            if (totalPages <= maxPagesToShow) {
                for (let i = 1; i <= totalPages; i++) pages.push(i);
            } else {
                let startPage = Math.max(1, currentPage - Math.floor(maxPagesToShow / 2));
                let endPage = Math.min(totalPages, startPage + maxPagesToShow - 1);
                if (endPage - startPage + 1 < maxPagesToShow) {
                    startPage = Math.max(1, endPage - maxPagesToShow + 1);
                }
                for (let i = startPage; i <= endPage; i++) pages.push(i);
            }
            return pages;
        },
        rootCategories() { 
            if (!this.categories) return [];
            return this.categories.filter(c => !c.parent_id).map(rc => ({ 
                ...rc, 
                subcategories: this.categories.filter(sub => sub.parent_id === rc.id) 
            }));
        },
        currentFormulaTotalQuantity() {
            if (!this.currentFormula || !this.currentFormula.ingredients) return 0;
            return this.currentFormula.ingredients.reduce((sum, item) => sum + (parseFloat(item.quantity) || 0), 0);
        },
        currentFormulaTotalCost() {
            if (!this.currentFormula || !this.currentFormula.ingredients) return 0;
            return this.currentFormula.ingredients.reduce((sum, item) => {
                const cost = parseFloat(item.cost_per_unit) || 0;
                const quantity = parseFloat(item.quantity) || 0;
                return sum + (cost * quantity);
            }, 0);
        },
        sortedIngredients() {
            if (!this.ingredients) return [];
            return [...this.ingredients].map(ing => ({
                ...ing, 
                editBuffer: ing.editBuffer || {} 
            })).sort((a, b) => {
                let valA = a[this.sortKey];
                let valB = b[this.sortKey];
                if (this.sortKey === 'categoriesDisplay') { 
                    valA = a.categories && a.categories.length > 0 ? a.categories.map(c => c.name).join(',').toLowerCase() : '';
                    valB = b.categories && b.categories.length > 0 ? b.categories.map(c => c.name).join(',').toLowerCase() : '';
                } else if (typeof valA === 'string') {
                    valA = valA.toLowerCase();
                    valB = (typeof valB === 'string') ? valB.toLowerCase() : (valB === null || typeof valB === 'undefined' ? '' : String(valB).toLowerCase()); 
                } else if (typeof valA === 'number' || typeof valB === 'number') {
                    valA = (valA === null || typeof valA === 'undefined') ? (this.sortAsc ? Infinity : -Infinity) : Number(valA);
                    valB = (valB === null || typeof valB === 'undefined') ? (this.sortAsc ? Infinity : -Infinity) : Number(valB);
                }
                if (valA < valB) return this.sortAsc ? -1 : 1;
                if (valA > valB) return this.sortAsc ? 1 : -1;
                return 0;
            });
        },
        currentAIServiceModels() {
            // This computed property now correctly reflects the dynamically loaded or fallback models
            if (this.aiSelectedService === 'gemini') return this.geminiModels;
            if (this.aiSelectedService === 'openrouter') return this.openrouterModels;
            if (this.aiSelectedService === 'claude') return this.claudeModels;
            return [];
        },
    }, 
    mounted() { 
        this.initializeDarkMode(); 
        this.loadInitialData(); 
        this.setupEventListeners(); 
        window.addEventListener('resize', this.handleWindowResize);
        this.loadApiKeysFromStorage(); 
        this.loadDefaultPrompts(); 
        this.loadSavedPrompts(); 
        this.loadFallbackAIModels(); // Load fallbacks initially
    }, 
    beforeUnmount() {
        window.removeEventListener('resize', this.handleWindowResize);
        if (this.resizeDebounceTimer) clearTimeout(this.resizeDebounceTimer);
        if (this.searchDebounceTimer) clearTimeout(this.searchDebounceTimer);
    }, 
    methods: {
        // --- DARK MODE METHODS ---
        initializeDarkMode() {
            const storedPreference = localStorage.getItem('darkMode');
            if (storedPreference !== null) {
                this.isDarkMode = storedPreference === 'true';
            } else {
                this.isDarkMode = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
            }
            this.applyDarkMode();
        },
        toggleDarkMode() {
            this.isDarkMode = !this.isDarkMode;
            localStorage.setItem('darkMode', this.isDarkMode);
            this.applyDarkMode();
        },
        applyDarkMode() {
            if (this.isDarkMode) {
                document.body.classList.add('dark-mode');
            } else {
                document.body.classList.remove('dark-mode');
            }
        },
        
        // --- DATA LOADING ---
        loadInitialData() { 
            this.loadIngredients(); 
            this.loadCategories(); 
            this.fetchAllIngredientsForSelection(); 
            this.loadFormulas(); 
            // Fallback models are loaded in mounted, dynamic fetch happens on service change/manual trigger
        },
        loadFallbackAIModels(){ 
            axios.get('/api/ai/models') 
            .then(r => {
                this.openrouterModels = r.data.openrouter || [];
                this.geminiModels = r.data.gemini || [];
                this.claudeModels = r.data.claude || [];
                // Set a default selected model if none is selected for the current service
                this.updateSelectedModelForCurrentService();
            }).catch(e => {
                console.error('Error loading fallback AI models:', e);
                // Ensure model arrays are empty if fetch fails, to avoid errors
                this.openrouterModels = [];
                this.geminiModels = [];
                this.claudeModels = [];
            });
        },
        updateSelectedModelForCurrentService() {
            const currentModels = this.currentAIServiceModels;
            if (currentModels.length > 0) {
                // Check if the currently selected model is still valid for the new list
                const modelExists = currentModels.some(m => m.id === this.aiSelectedModel);
                if (!modelExists || !this.aiSelectedModel) {
                    this.aiSelectedModel = currentModels[0].id; // Default to the first model
                }
            } else {
                this.aiSelectedModel = ''; // No models available
            }
        },

        // --- INGREDIENT METHODS ---
        triggerSearch() { 
            this.ingredientPagination.page = 1; 
            if (this.searchDebounceTimer) { 
                clearTimeout(this.searchDebounceTimer); 
                this.searchDebounceTimer = null; 
            } 
            this.loadIngredients(); 
        },
        loadIngredients() {
            if (this.searchDebounceTimer) { 
                clearTimeout(this.searchDebounceTimer); 
                this.searchDebounceTimer = null; 
            }
            const params = { 
                page: this.ingredientPagination.page, 
                per_page: this.ingredientPagination.per_page, 
                sort_by: this.sortKey, 
                sort_direction: this.sortAsc ? 'asc' : 'desc' 
            };
            const searchTermTrimmed = this.ingredientSearch ? this.ingredientSearch.trim() : '';
            if (searchTermTrimmed) params.search = searchTermTrimmed;
            if (this.ingredientCategoryFilter) params.category_id = this.ingredientCategoryFilter;
            
            axios.get('/api/ingredients', { params })
            .then(response => {
                this.ingredients = response.data.items.map(ing => ({ ...ing, isEditing: false, isEditingAmount: false, editBuffer: {} }));
                this.ingredientPagination = response.data.pagination; 
                this.lastUpdatedTimestamp = new Date().toISOString(); 
                if (!this.initialPerPageAdjustDone && this.currentMainView === 'ingredients') { 
                    this.$nextTick(() => { this.adjustPerPageItems(); }); 
                } else if (this.currentMainView !== 'ingredients' && !this.initialPerPageAdjustDone) {
                    this.initialPerPageAdjustDone = true;
                }
            })
            .catch(error => { 
                console.error('Error loading ingredients:', error.response?.data || error.message || error); 
                this.ingredients = []; 
                this.ingredientPagination = { page: 1, per_page: this.minPerPage, total_pages: 0, total_items: 0 }; 
            });
        },
        async getElementHeight(selector) { 
            await this.$nextTick(); 
            const e = document.querySelector(selector); 
            return e ? e.offsetHeight : 0; 
        },
        async adjustPerPageItems() {
            if (this.currentMainView !== 'ingredients') {
                if (!this.initialPerPageAdjustDone) this.initialPerPageAdjustDone = true;
                return;
            }
            await this.$nextTick(); 
            const mc = document.querySelector('.main-content'); 
            if (!mc) {
                console.warn("'.main-content' not found for per-page adjustment."); 
                 if (!this.initialPerPageAdjustDone) this.initialPerPageAdjustDone = true;
                return;
            }
            const mcs = window.getComputedStyle(mc); 
            const padT = parseFloat(mcs.paddingTop) || 0; 
            const padB = parseFloat(mcs.paddingBottom) || 0;
            const mchH = await this.getElementHeight('.main-content .main-content-header');
            const tthH = await this.getElementHeight('.main-content .resizable-table thead.sticky-thead');
            const pgnH = await this.getElementHeight('.main-content nav[aria-label="Ingredient pagination"]'); 
            const bBuf = 10; 
            const cbH = mc.clientHeight - padT - padB;
            const avH = cbH - mchH - tthH - pgnH - bBuf;
            
            if (avH > 0 && this.estimatedRowHeight > 0) {
                let npp = Math.floor(avH / this.estimatedRowHeight); 
                npp = Math.max(this.minPerPage, npp);
                const ppc = npp !== this.ingredientPagination.per_page;
                if (ppc || !this.initialPerPageAdjustDone) {
                    const pact = this.ingredientPagination.page !== 1 || !this.initialPerPageAdjustDone;
                    this.ingredientPagination.per_page = npp;
                    if (ppc || pact) this.ingredientPagination.page = 1; 
                    this.initialPerPageAdjustDone = true; 
                    this.loadIngredients();
                }
            } else { 
                if (!this.initialPerPageAdjustDone) { 
                    this.ingredientPagination.per_page = Math.max(this.ingredientPagination.per_page, this.minPerPage); 
                    this.initialPerPageAdjustDone = true; 
                    if (this.ingredients.length === 0 && this.ingredientPagination.total_items === 0) this.loadIngredients(); 
                } else if (this.ingredientPagination.per_page < this.minPerPage) { 
                    this.ingredientPagination.per_page = this.minPerPage; 
                    if (this.ingredientPagination.page !== 1) this.ingredientPagination.page = 1; 
                    this.loadIngredients();
                }
            }
        },
        handleWindowResize() { 
            if (this.resizeDebounceTimer) clearTimeout(this.resizeDebounceTimer); 
            this.resizeDebounceTimer = setTimeout(() => {
                if (this.currentMainView === 'ingredients') {
                    this.initialPerPageAdjustDone = false; 
                    this.adjustPerPageItems();
                }
            }, 300); 
        },
        changePage(p) { 
            if (p >= 1 && p <= this.ingredientPagination.total_pages && p !== this.ingredientPagination.page) { 
                this.ingredientPagination.page = p; 
                this.loadIngredients(); 
            } 
        },
        sortIngredients(k) { 
            if (this.sortKey === k) this.sortAsc = !this.sortAsc; 
            else { this.sortKey = k; this.sortAsc = true; } 
            this.ingredientPagination.page = 1; 
            this.loadIngredients(); 
        },
        getSortIcon(k) { 
            if (this.sortKey !== k) return 'bi-arrow-down-up text-muted'; 
            return this.sortAsc ? 'bi-sort-up-alt' : 'bi-sort-down'; 
        },
        clearFiltersAndSort() { 
            this.ingredientSearch = ''; 
            this.ingredientCategoryFilter = ''; 
            this.sortKey = 'name'; 
            this.sortAsc = true; 
            this.triggerSearch(); 
        },
        addIngredientFromPanel() { 
            if (!this.newIngredientPanel.name.trim()) { alert('Name required.'); return; } 
            if (this.newIngredientPanel.category_ids.length > 3) { alert('Max 3 cats.'); return; } 
            const p = { 
                name: this.newIngredientPanel.name, 
                stock_quantity: this.newIngredientPanel.amount, 
                unit_of_measurement: this.newIngredientPanel.unit, 
                category_ids: this.newIngredientPanel.category_ids, 
                notes: this.newIngredientPanel.notes, 
                description:'', supplier:'', cost_per_unit:null
            }; 
            axios.post('/api/ingredients',p)
            .then(r => {
                this.loadIngredients(); 
                this.newIngredientPanel = {name:'', amount:null, unit:'g', category_ids:[], notes:''}; 
                alert(r.data.message || 'Added!');
            })
            .catch(e => alert('Failed: ' + (e.response?.data?.error || e.message))); 
        },
        startEditing(ing) { 
            if (this.editingIngredientId !== null && this.editingIngredientId !== ing.id) { 
                const cur = this.ingredients.find(i => i.id === this.editingIngredientId); 
                if (cur) this.cancelEditing(cur, true); 
            } 
            this.editingIngredientId = ing.id; 
            ing.editBuffer = JSON.parse(JSON.stringify(ing)); 
            ing.editBuffer.category_ids = ing.categories ? ing.categories.map(c => c.id) : []; 
            ing.isEditing = true; 
            ing.isEditingAmount = false; 
            this.$nextTick(() => {
                const el = document.querySelector(`#ingredient-row-${ing.id} input[type='text'], #ingredient-row-${ing.id} select, #ingredient-row-${ing.id} textarea`); 
                if (el) el.focus();
            }); 
        },
        startEditingAmount(ing) { 
            if (this.editingIngredientId !== null && this.editingIngredientId !== ing.id) { 
                const cur = this.ingredients.find(i => i.id === this.editingIngredientId); 
                if (cur) this.cancelEditing(cur, true); 
            } 
            this.editingIngredientId = ing.id; 
            ing.editBuffer = JSON.parse(JSON.stringify(ing)); 
            ing.isEditing = false; 
            ing.isEditingAmount = true; 
            this.$nextTick(() => {
                const el = document.querySelector(`#ingredient-row-${ing.id} input[type='number']`); 
                if (el) el.focus();
            }); 
        },
        saveInlineEdit(ing) { 
            if (!ing || !ing.editBuffer) return; 
            if (ing.isEditing && (!ing.editBuffer.name || ing.editBuffer.name.trim() === '')) {
                alert("Name required."); return;
            } 
            const nf = ['cost_per_unit', 'stock_quantity', 'minimum_stock_threshold']; 
            for (const f of nf) {
                if (ing.editBuffer[f] !== null && String(ing.editBuffer[f]).trim() !== '') {
                    let vs = String(ing.editBuffer[f]).replace(/[^0-9.-]+/g,""); 
                    if (vs === '' || isNaN(parseFloat(vs))) {
                        alert(`Invalid ${f}.`); return;
                    } 
                    ing.editBuffer[f] = parseFloat(vs);
                } else if (String(ing.editBuffer[f]).trim() === '') {
                    ing.editBuffer[f] = null;
                }
            } 
            const p = {...ing.editBuffer}; 
            if (ing.isEditing) p.category_ids = ing.editBuffer.category_ids || (ing.categories ? ing.categories.map(c => c.id) : []); 
            delete p.isEditing; 
            delete p.isEditingAmount; 
            delete p.categories; 
            delete p.editBuffer; 
            axios.put(`/api/ingredients/${ing.id}`, p)
            .then(r => {
                const uD = r.data.ingredient || r.data; 
                const idx = this.ingredients.findIndex(i => i.id === ing.id); 
                if (idx !== -1) {
                    Object.assign(this.ingredients[idx], uD); 
                    this.ingredients[idx].isEditing = false; 
                    this.ingredients[idx].isEditingAmount = false; 
                    this.ingredients[idx].editBuffer = {};
                } else {
                    this.loadIngredients();
                } 
                this.editingIngredientId = null; 
                alert(r.data.message || 'Updated!');
            })
            .catch(e => alert('Save failed: ' + (e.response?.data?.error || e.message))); 
        },
        cancelEditing(ing, auto = false) {
            if (ing) {
                ing.isEditing = false; 
                ing.isEditingAmount = false; 
                ing.editBuffer = {};
            } 
            if (this.editingIngredientId === ing.id || auto) this.editingIngredientId = null;
        },
        displayAmountAndUnit(ing) {
            const q = ing.stock_quantity; 
            const u = ing.unit_of_measurement; 
            const su = ['g', 'mL', 'oz', 'drops'];
            let qd = (q !== null && typeof q !== 'undefined') ? q : "N/A";
            if (u && typeof u === 'string') {
                const ul = u.toLowerCase();
                if (su.includes(u)) return `${qd}${u}`;
                if (ul.includes("not specified")) return `Size not Specified (Amount ${qd}?)`;
                if (q === 1 || qd === "N/A") return `<span class="unit-value">${u}</span>`;
                return `<span class="amount-value">${qd}</span> <span class="times-symbol">&times;</span> <span class="unit-value">${u}</span>`;
            }
            if (qd !== "N/A") return `<span class="amount-value">${qd}</span>`;
            return `<span class="amount-value">N/A</span>`;
        },
        formatNotes(n) {
            if (n === null || typeof n === 'undefined' || (typeof n === 'string' && n.trim() === '')) return '';
            if (typeof n === 'string') {
                if (n.trim() === "[]") return '';
                if (n.startsWith("['") && n.endsWith("']")) {
                    try {
                        const j = n.replace(/'/g, '"');
                        const p = JSON.parse(j);
                        if (Array.isArray(p)) {
                            if (p.length === 0) return '';
                            return p.join(', ');
                        }
                    } catch (e) {
                        let cl = n.substring(2, n.length - 2).replace(/',\s*'/g, ', ');
                        if (cl.trim() === '') return '';
                        return cl;
                    }
                }
            }
            return String(n);
        },
        deleteIngredient(id) { 
            if (confirm('Delete?')) {
                axios.delete(`/api/ingredients/${id}`)
                .then(() => {
                    this.loadIngredients(); 
                    alert('Deleted.');
                })
                .catch(e => alert('Failed: ' + (e.response?.data?.error || e.message))); 
            }
        },
        toggleSelectAllIngredients(event) { 
            this.selectedIngredientIds = event.target.checked ? this.sortedIngredients.map(ing => ing.id) : []; 
        },
        promptDeleteSelectedIngredients() { 
            if (!this.selectedIngredientIds.length) { alert("None selected."); return; } 
            if (confirm(`Delete ${this.selectedIngredientIds.length} items?`)) this.deleteSelectedIngredients(); 
        },
        deleteSelectedIngredients() { 
            axios.post('/api/ingredients/delete-selected', { ids: this.selectedIngredientIds })
            .then(res => { 
                alert(res.data.message); 
                this.selectedIngredientIds = []; 
                this.loadIngredients(); 
            })
            .catch(e => alert('Failed: ' + (e.response?.data?.error || e.message))); 
        },
        promptDeleteAllIngredients() { 
            if (!this.ingredients.length) { alert("No items to delete."); return; } 
            if (confirm('DELETE ALL ingredients? Irreversible.')) {
                if (confirm('Confirm permanent deletion of ALL items?')) this.deleteAllIngredients(); 
            }
        },
        deleteAllIngredients() { 
            axios.delete('/api/ingredients/all')
            .then(res => { 
                alert(res.data.message); 
                this.loadIngredients(); 
                this.selectedIngredientIds = []; 
            })
            .catch(e => alert('Failed: ' + (e.response?.data?.error || e.message))); 
        },
        viewIngredient(id) { 
            const ing = this.ingredients.find(i => i.id === id); 
            if (ing) { 
                if (this.editingIngredientId) this.cancelEditing(this.ingredients.find(i => i.id === this.editingIngredientId), true); 
                this.viewedIngredient = { ...ing }; 
                const modalEl = document.getElementById('viewIngredientModal');
                if (modalEl) {
                    (bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl)).show();
                }
            } 
        },

        // --- CATEGORY METHODS ---
        loadCategories() { 
            axios.get('/api/categories')
            .then(res => this.categories = res.data)
            .catch(e => console.error('Load categories error:', e)); 
        },
        navigateToManageCategories() { 
            this.loadCategories(); 
            this.editingCategoryId = null; 
            this.showAddCategoryForm = false; 
            this.newCategory = { name: '', description: '', parent_id: null }; 
            const el = document.getElementById('manageCategoriesModal'); 
            if (el) (bootstrap.Modal.getInstance(el) || new bootstrap.Modal(el)).show(); 
            else alert("Category modal UI not found."); 
        },
        showAddCategoryInlineForm() { 
            this.cancelCategoryEdit(); 
            this.newCategory = { name: '', description: '', parent_id: null }; 
            this.showAddCategoryForm = true; 
            this.$nextTick(() => document.getElementById('newCatName')?.focus()); 
        },
        cancelAddCategoryInline() { 
            this.showAddCategoryForm = false; 
            this.newCategory = { name: '', description: '', parent_id: null }; 
        },
        saveNewInlineCategory() { 
            if (!this.newCategory.name.trim()) { alert('Category name needed.'); return; } 
            axios.post('/api/categories', this.newCategory)
            .then(res => { 
                alert(res.data.message); 
                this.loadCategories(); 
                this.cancelAddCategoryInline(); 
            })
            .catch(e => alert('Failed: ' + (e.response?.data?.error || e.message))); 
        },
        startCategoryEdit(cat) { 
            this.cancelAddCategoryInline(); 
            this.editingCategoryId = cat.id; 
            this.categoryEditBuffer = JSON.parse(JSON.stringify(cat)); 
            if (!this.categoryEditBuffer.parent_id) this.categoryEditBuffer.parent_id = null; 
        },
        cancelCategoryEdit() { 
            this.editingCategoryId = null; 
            this.categoryEditBuffer = { id: null, name: '', description: '', parent_id: null }; 
        },
        saveCategoryEdit() { 
            if (!this.categoryEditBuffer.name.trim()) { alert('Category name needed.'); return; } 
            if (this.categoryEditBuffer.id === this.categoryEditBuffer.parent_id && this.categoryEditBuffer.parent_id !== null) { 
                alert('Cannot be own parent.'); return; 
            } 
            const payload = { 
                name: this.categoryEditBuffer.name, 
                description: this.categoryEditBuffer.description, 
                parent_id: this.categoryEditBuffer.parent_id 
            }; 
            axios.put(`/api/categories/${this.editingCategoryId}`, payload)
            .then(res => { 
                alert(res.data.message); 
                this.loadCategories(); 
                this.cancelCategoryEdit(); 
            })
            .catch(e => alert('Failed: ' + (e.response?.data?.error || e.message))); 
        },
        confirmDeleteCategory(id) { 
            const cat = this.categories.find(c => c.id === id); 
            if (!cat) return; 
            if (cat.ingredient_count > 0) { 
                alert(`Cannot delete "${cat.name}": ${cat.ingredient_count} ingredients assigned.`); return; 
            } 
            if (confirm(`Delete category "${cat.name}"?`)) this.deleteCategory(id); 
        },
        deleteCategory(id) { 
            axios.delete(`/api/categories/${id}`)
            .then(res => { 
                alert(res.data.message); 
                this.loadCategories(); 
                this.loadIngredients(); 
            })
            .catch(e => alert('Failed: ' + (e.response?.data?.error || e.message))); 
        },
        getCategoryNameById(id) { 
            if (!id) return ''; 
            const cat = this.categories.find(c => c.id === id); 
            return cat ? cat.name : 'Unknown'; 
        },
        promptResetCategoriesToDefaults() { 
            if (confirm('RESET ALL CATEGORIES TO DEFAULTS? Deletes current categories and unassigns items.')) {
                if (confirm('Confirm IRREVERSIBLE category data reset?')) {
                    axios.post('/api/categories/reset-to-defaults')
                    .then(res => { 
                        alert(res.data.message); 
                        this.loadCategories(); 
                        this.loadIngredients(); 
                    })
                    .catch(e => alert('Failed: ' + (e.response?.data?.error || e.message))); 
                }
            }
        },

        // --- IMPORT/EXPORT METHODS ---
        navigateToImportData() { 
            this.importFile = null; 
            this.importFileObject = null; 
            this.rawFileContent = null; 
            this.importAnalysis = {format:'', structure:'', fields:[], item_count:0, sample_data:[], mapping_suggestion:{}, main_array_key:null, message:'', data_path:''}; 
            this.importMapping = {}; 
            this.importStatus = ''; 
            this.importSuccess = false; 
            this.importErrors = []; 
            this.categoryWarnings = []; 
            this.isAnalyzingFile = false; 
            this.fileAnalyzedSuccessfully = false; 
            const fi = document.getElementById('importFileInputModal'); 
            if (fi) fi.value = ''; 
            const modal = document.getElementById('importDataModal'); 
            if (modal) (bootstrap.Modal.getInstance(modal) || new bootstrap.Modal(modal)).show(); 
            else alert("Import UI error."); 
        },
        exportData(format) { 
            if (format === 'json') {
                if (!this.ingredients.length) { alert("Nothing to export."); return; } 
                const str = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(this.ingredients, null, 2)); 
                const a = document.createElement('a'); 
                a.href = str; 
                a.download = "ingredients.json"; 
                document.body.appendChild(a); 
                a.click(); 
                document.body.removeChild(a); 
                alert("Exported as JSON.");
            } else if (format === 'csv') {
                alert("CSV export: backend recommended for full data.");
            }
        },
        handleFileUpload(event) {
            this.importFile = event.target.files[0];
            this.importFileObject = this.importFile;
            this.importAnalysis = {format:'', structure:'', fields:[], item_count:0, sample_data:[], mapping_suggestion:{}, main_array_key:null, message:'', data_path:''};
            this.importMapping = {};
            this.importStatus = '';
            this.importErrors = [];
            this.categoryWarnings = [];
            this.fileAnalyzedSuccessfully = false;
            if (this.importFile) {
                const r = new FileReader();
                r.onload = e => {
                    this.rawFileContent = e.target.result;
                    this.analyzeFile(); 
                };
                r.onerror = e => {
                    this.importStatus = "Error reading file.";
                    this.importErrors = ["Could not read file."];
                };
                r.readAsText(this.importFile);
            }
        },
        analyzeFile() {
            if (!this.importFile) { this.importStatus = 'Select file.'; return; }
            this.isAnalyzingFile = true;
            this.importStatus = 'Analyzing...';
            this.importErrors = [];
            this.categoryWarnings = [];
            this.fileAnalyzedSuccessfully = false;
            this.importAnalysis = {format:'', structure:'', fields:[], item_count:0, sample_data:[], mapping_suggestion:{}, main_array_key:null, message:'', data_path:''};
            this.importMapping = {};
            const fd = new FormData();
            fd.append('file', this.importFile);
            axios.post('/api/import/analyze', fd, { headers: {'Content-Type': 'multipart/form-data'} })
            .then(res => {
                if (res.data && res.data.fields !== undefined && Array.isArray(res.data.fields) && res.data.sample_data !== undefined && Array.isArray(res.data.sample_data)) {
                    this.importAnalysis = res.data;
                    this.importStatus = `Analyzed: ${this.importAnalysis.item_count || 0} items.`;
                    this.fileAnalyzedSuccessfully = true;
                    this.importMapping = {...(this.importAnalysis.mapping_suggestion || {})};
                } else {
                    const err = res.data?.error || res.data?.message || 'Analysis incomplete.';
                    this.importStatus = 'Error: Incomplete data.';
                    this.importErrors = [err];
                    this.fileAnalyzedSuccessfully = false;
                }
            })
            .catch(e => {
                let err = 'Unknown analysis error.';
                if (e.response?.data?.error) err = e.response.data.error;
                else if (typeof e.response?.data === 'string') err = e.response.data;
                else if (e.message) err = e.message;
                this.importStatus = 'Error analyzing.';
                this.importErrors = [err];
                this.fileAnalyzedSuccessfully = false;
            })
            .finally(() => this.isAnalyzingFile = false);
        },
        processImport() {
            if (!this.importAnalysis || !this.rawFileContent || !this.fileAnalyzedSuccessfully) { 
                this.importStatus = 'Analyze file first.'; return; 
            }
            this.importStatus = 'Processing...';
            this.importErrors = [];
            this.categoryWarnings = [];
            this.importSuccess = false;
            const p = {
                mapping: this.importMapping,
                import_type: this.importType,
                format: this.importAnalysis.format,
                raw_file_content: this.rawFileContent, 
                main_array_key: this.importAnalysis.main_array_key 
            };
            axios.post('/api/import/process', p)
            .then(res => {
                this.importStatus = res.data.message || 'Import complete.';
                this.importSuccess = res.data.success || false;
                this.importErrors = res.data.errors || [];
                this.categoryWarnings = res.data.category_warnings || [];
                if (res.data.imported_count > 0) this.loadIngredients(); 
            })
            .catch(e => {
                this.importStatus = 'Error processing.';
                this.importErrors = [e.response?.data?.error || 'Unknown import error.'];
                this.importSuccess = false;
            });
        },
        formatFieldName(f) { 
            if (!f) return ''; 
            return f.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()); 
        },
        batchUpdateNotes() { 
            if (!this.selectedIngredientIds.length) { alert("None selected."); return; } 
            const n = prompt(`Notes for ${this.selectedIngredientIds.length} items:`); 
            if (n !== null) {
                axios.post('/api/ingredients/batch-update', {ids: this.selectedIngredientIds, notes: n})
                .then(r => {
                    alert(r.data.message); 
                    this.loadIngredients(); 
                    this.selectedIngredientIds = [];
                })
                .catch(e => alert('Failed: ' + (e.response?.data?.error || e.message))); 
            }
        },
        batchUpdateCategories() { 
            if (!this.selectedIngredientIds.length) { alert("None selected."); return; } 
            this.batchCategoriesToApply = []; 
            const m = document.getElementById('batchCategoryModal'); 
            if (m) (bootstrap.Modal.getInstance(m) || new bootstrap.Modal(m)).show(); 
            else alert("Batch category UI error."); 
        },
        applyBatchCategoryUpdate() { 
            if (!this.selectedIngredientIds.length) { this.closeModal('batchCategoryModal'); return; } 
            axios.post('/api/ingredients/batch-update', {ids: this.selectedIngredientIds, category_ids: this.batchCategoriesToApply})
            .then(r => {
                alert(r.data.message); 
                this.loadIngredients(); 
                this.selectedIngredientIds = []; 
                this.closeModal('batchCategoryModal');
            })
            .catch(e => {
                alert('Failed: ' + (e.response?.data?.error || e.message)); 
                this.closeModal('batchCategoryModal');
            }); 
        },

        // --- AI & API KEY METHODS ---
        openApiSettingsModal() {
            this.apiKeySaveStatus = ''; 
            const modalEl = document.getElementById('apiSettingsModal');
            if (modalEl) {
                this.apiSettingsModalInstance = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
                this.apiSettingsModalInstance.show();
            } else {
                console.error("API Settings modal element not found");
                alert("API Settings UI is currently unavailable.");
            }
        },
        closeApiSettingsModal() {
            if (this.apiSettingsModalInstance) {
                this.apiSettingsModalInstance.hide();
            }
        },
        loadApiKeysFromStorage() {
            const storedKeys = localStorage.getItem('perfumeryApiKeys');
            if (storedKeys) {
                try {
                    const parsedKeys = JSON.parse(storedKeys);
                    this.apiKeys.openrouter = parsedKeys.openrouter || '';
                    this.apiKeys.gemini = parsedKeys.gemini || '';
                    this.apiKeys.claude = parsedKeys.claude || '';
                } catch(e) {
                    console.error("Error parsing stored API keys:", e);
                    this.apiKeys = { openrouter: '', gemini: '', claude: '' };
                }
            }
        },
        saveApiKeys() {
            try {
                localStorage.setItem('perfumeryApiKeys', JSON.stringify(this.apiKeys));
                this.apiKeySaveStatus = 'API Keys saved successfully!';
                // Attempt to fetch models for services that now have a key
                ['openrouter', 'gemini', 'claude'].forEach(service => {
                    if (this.apiKeys[service] && 
                        ((service === 'openrouter' && this.openrouterModels.length === 0) || 
                         (service === 'gemini' && this.geminiModels.length === 0) ||
                         (service === 'claude' && this.claudeModels.length === 0) ||
                         this.openrouterModels.every(m => m.name.includes("Fallback")) && service === 'openrouter' // Re-fetch if only fallback
                        )) {
                        this.fetchModelsForService(service, true); // true to indicate it's an auto-fetch
                    }
                });
                setTimeout(() => this.apiKeySaveStatus = '', 3000); 
            } catch (e) {
                console.error("Error saving API keys to localStorage:", e);
                this.apiKeySaveStatus = 'Failed to save API Keys.';
                alert('Could not save API keys. Your browser might be configured to block local storage.');
            }
        },
        getApiKeyForService(serviceName) {
            if (serviceName && this.apiKeys[serviceName.toLowerCase()]) {
                 return this.apiKeys[serviceName.toLowerCase()];
            }
            return '';
        },
        fetchModelsForService(serviceToFetch = null, autoFetch = false) {
            const service = serviceToFetch || this.serviceToFetchModelsFor;
            if (!service) {
                this.modelFetchStatus = "Please select a service.";
                if (!autoFetch) setTimeout(() => this.modelFetchStatus = '', 5000);
                return;
            }
            const apiKey = this.getApiKeyForService(service);
            if (!apiKey) {
                this.modelFetchStatus = `API key for ${service} is not set. Please add it in API Key Settings.`;
                 if (!autoFetch) setTimeout(() => this.modelFetchStatus = '', 7000);
                return;
            }
            this.modelFetchStatus = `Fetching models for ${service}...`;
            
            axios.post('/api/ai/fetch-service-models', { service: service, api_key: apiKey })
                .then(response => {
                    if (response.data.success && response.data.models) {
                        if (service === 'openrouter') this.openrouterModels = response.data.models;
                        else if (service === 'gemini') this.geminiModels = response.data.models;
                        else if (service === 'claude') this.claudeModels = response.data.models;
                        
                        this.modelFetchStatus = `Models for ${service} updated. ${response.data.message || ''}`;
                        this.updateSelectedModelForCurrentService(); // Update selection after new models are loaded
                    } else {
                        this.modelFetchStatus = `Error fetching models for ${service}: ${response.data.error || 'Unknown error'}`;
                        // If fetch fails, ensure we still have the fallback list for the current selection
                        if (service === this.aiSelectedService) {
                            this.loadFallbackAIModelsForService(service);
                        }
                    }
                })
                .catch(error => {
                    this.modelFetchStatus = `Error fetching models for ${service}: ${error.response?.data?.error || error.message}`;
                    if (service === this.aiSelectedService) {
                        this.loadFallbackAIModelsForService(service); // Load fallback on catch
                    }
                })
                .finally(() => {
                    if (!autoFetch) setTimeout(() => this.modelFetchStatus = '', 7000);
                });
        },
        loadFallbackAIModelsForService(serviceName) {
            // Helper to load only the specific service's fallback models
            axios.get('/api/ai/models') 
            .then(r => {
                if (serviceName === 'openrouter') this.openrouterModels = r.data.openrouter || [];
                else if (serviceName === 'gemini') this.geminiModels = r.data.gemini || [];
                else if (serviceName === 'claude') this.claudeModels = r.data.claude || [];
                this.updateSelectedModelForCurrentService();
            }).catch(e => console.error(`Error loading fallback AI models for ${serviceName}:`, e));
        },

        toggleGlobalAIChat() { 
            const m = document.getElementById('globalAiChatModal'); 
            if (m) (bootstrap.Modal.getInstance(m) || new bootstrap.Modal(m)).show(); 
            else alert("AI Chat modal not found."); 
        },
        showAIContextPanel(type, id) { 
            if (type === 'ingredient') this.contextualAIItem = this.ingredients.find(i => i.id === id); 
            if (this.contextualAIItem) this.showContextualAIPanel = true; 
        },
        hideAIContextPanel() { 
            this.showContextualAIPanel = false; 
            this.contextualAIItem = null; 
        },
        loadDefaultPrompts() { 
            axios.get('/api/ai/default-prompts')
            .then(r => {
                this.openrouterSystemPrompt = r.data.openrouter || ''; 
                this.geminiSystemPrompt = r.data.gemini || ''; 
                this.claudeSystemPrompt = r.data.claude || '';
            })
            .catch(e => console.error("Error loading default prompts", e)); 
        },
        resetSystemPrompt(s) { 
            axios.get('/api/ai/default-prompts')
            .then(r => {
                if (s === 'openrouter') this.openrouterSystemPrompt = r.data.openrouter || ''; 
                else if (s === 'gemini') this.geminiSystemPrompt = r.data.gemini || ''; 
                else if (s === 'claude') this.claudeSystemPrompt = r.data.claude || '';
            })
            .catch(e => console.error("Error resetting prompt", e)); 
        },
        loadSavedPrompts() { 
            axios.get('/api/ai/saved-prompts')
            .then(r => this.savedPrompts = r.data || [])
            .catch(e => console.error("Error loading saved prompts", e)); 
        },
        loadSavedPrompt(p) { 
            if (!p) return; 
            this.aiSelectedService = p.service; // This will trigger the watcher
            this.$nextTick(() => { // Ensure model list for the service is populated before setting model
                this.aiSelectedModel = p.model;
                // Assign system prompt based on the service from the saved prompt
                if (p.service === 'openrouter') this.openrouterSystemPrompt = p.system_prompt;
                else if (p.service === 'gemini') this.geminiSystemPrompt = p.system_prompt;
                else if (p.service === 'claude') this.claudeSystemPrompt = p.system_prompt;
                
                this.aiFormulaUserDescription = p.user_prompt; 
                alert(`Loaded prompt: ${p.name}. Service, model, and user description populated.`); 
            });
        },
        saveCurrentPrompt(s) { this.currentPromptService = s; this.newPromptName = ''; alert("Save Prompt: Needs modal for name input."); }, 
        confirmSavePrompt() { alert("Confirm Save: Needs impl."); }, 
        
        // --- GENERAL UI & UTILITY METHODS ---
        setupEventListeners() { 
            document.addEventListener('mousemove', this.handleMouseMove); 
            document.addEventListener('mouseup', this.handleMouseUp); 
        }, 
        startResize(e, idx) { 
            this.resizing = true; 
            this.resizingColumn = e.target.closest('th'); 
            this.startX = e.pageX; 
            this.startWidth = this.resizingColumn.offsetWidth; 
            e.preventDefault(); 
        },
        handleMouseMove(e) {
            if (!this.resizing || !this.resizingColumn) return; 
            const dX = e.pageX - this.startX; 
            const nW = this.startWidth + dX; 
            if (nW > 50) this.resizingColumn.style.width = `${nW}px`; 
        }, 
        handleMouseUp() {
            if (this.resizing) {
                this.resizing = false; 
                this.resizingColumn = null;
            }
        },
        formatCurrency(v) {
            if (v === null || typeof v === 'undefined' || String(v).trim() === '') return ''; 
            try {
                 return new Intl.NumberFormat('en-US', {style: 'currency', currency: 'USD'}).format(parseFloat(v));
            } catch (e) {
                return String(v); 
            }
        }, 
        formatDate(d) {
            if (!d) return 'N/A'; 
            try {
                const o = {year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'}; 
                return new Date(d).toLocaleDateString(undefined, o);
            } catch (e) {
                return d;
            }
        },
        closeModal(id) {
            const el = document.getElementById(id); 
            if (el) {
                const i = bootstrap.Modal.getInstance(el); 
                if (i) i.hide(); 
                else {
                    try { new bootstrap.Modal(el).hide(); } 
                    catch (e) { console.warn("Could not hide modal:", id, e); }
                }
            } else {
                console.warn("Modal not found:", id);
            }
        },
        getIngredientName(id) { 
            const i = this.allIngredientsForSelection.find(ing => ing.id === id); 
            return i ? i.name : 'Unknown Ingredient';
        },

        // --- FORMULA METHODS ---
        loadFormulas() {
            const params = {
                page: this.formulaPagination.page,
                per_page: this.formulaPagination.per_page, 
                search: this.formulaSearch.trim()
            };
            axios.get('/api/formulas', { params })
                .then(response => {
                    this.formulas = response.data.items;
                    this.formulaPagination = response.data.pagination;
                })
                .catch(error => {
                    console.error('Error loading formulas:', error.response?.data || error.message);
                    alert('Could not load formulas.');
                    this.formulas = [];
                    this.formulaPagination = { page: 1, per_page: 10, total_pages: 0, total_items: 0 };
                });
        },
        fetchAllIngredientsForSelection() { 
            axios.get('/api/ingredients', { params: { per_page: 10000 } }) 
                .then(response => {
                    this.allIngredientsForSelection = response.data.items.map(ing => ({
                        id: ing.id,
                        name: ing.name,
                        unit_of_measurement: ing.unit_of_measurement,
                        cost_per_unit: ing.cost_per_unit
                    }));
                })
                .catch(error => {
                    console.error('Error fetching all ingredients for selection:', error);
                    this.allIngredientsForSelection = []; 
                });
        },
        changeFormulaPage(page) {
            if (page >= 1 && page <= this.formulaPagination.total_pages && page !== this.formulaPagination.page) {
                this.formulaPagination.page = page;
                this.loadFormulas();
            }
        },
        triggerFormulaSearch() {
            this.formulaPagination.page = 1;
            this.loadFormulas();
        },
        openFormulaModal(mode, formula = null) {
            this.formulaModalMode = mode;
            this.aiFormulaUserDescription = ''; 
            this.aiGeneratedFormulaIngredients = [];
            this.aiFormulaError = '';
            this.aiTargetTotalQuantity = ''; // Reset target quantity

            if (mode === 'add') {
                this.currentFormula = {
                    name: '', description: '', creator: '', version: '1.0',
                    is_draft: true, notes: '', ingredients: []
                };
            } else if (mode === 'edit' && formula) {
                 axios.get(`/api/formulas/${formula.id}`)
                    .then(response => {
                        this.currentFormula = response.data;
                        this.currentFormula.ingredients = this.currentFormula.ingredients.map(fi => {
                            const masterIng = this.allIngredientsForSelection.find(i => i.id === fi.id); 
                            return {
                                ...fi, 
                                ingredient_id: fi.id, 
                                name: masterIng ? masterIng.name : 'Unknown Ingredient', 
                                cost_per_unit: masterIng ? masterIng.cost_per_unit : 0
                            };
                        });
                    })
                    .catch(error => {
                        alert('Error fetching formula details for editing.');
                        console.error(error);
                        return; 
                    });
            }
            const modalElement = document.getElementById('formulaModal');
            if (modalElement) {
                this.formulaModalInstance = bootstrap.Modal.getInstance(modalElement) || new bootstrap.Modal(modalElement);
                this.formulaModalInstance.show();
            } else {
                console.error("Formula modal element not found");
            }

            if (this.allIngredientsForSelection.length === 0) {
                 this.fetchAllIngredientsForSelection();
            }
            // Ensure a model is selected for the current AI service
            this.updateSelectedModelForCurrentService();
        },
        closeFormulaModal() {
            const modalElement = document.getElementById('formulaModal');
            if (modalElement) {
                const modalInstance = bootstrap.Modal.getInstance(modalElement);
                if (modalInstance) modalInstance.hide();
            }
        },
        addIngredientToCurrentFormula() {
            this.currentFormula.ingredients.push({
                ingredient_id: null, 
                name: '', 
                quantity: 0,
                unit: 'g', 
                percentage: 0, 
                notes: '',
                cost_per_unit: 0 
            });
        },
        removeIngredientFromCurrentFormula(index) {
            this.currentFormula.ingredients.splice(index, 1);
            this.recalculateFormulaPercentages();
        },
        onIngredientSelectInFormula(event, formulaIngredient) { 
            const selectedIngredientId = parseInt(event.target.value);
            const ingredient = this.allIngredientsForSelection.find(i => i.id === selectedIngredientId);
            if (ingredient) {
                formulaIngredient.ingredient_id = ingredient.id;
                formulaIngredient.unit = ingredient.unit_of_measurement || 'g';
                formulaIngredient.cost_per_unit = ingredient.cost_per_unit || 0;
            }
            this.recalculateFormulaPercentages();
        },
        recalculateFormulaPercentages() {
            const totalQuantity = this.currentFormulaTotalQuantity; 
            if (totalQuantity > 0) {
                this.currentFormula.ingredients.forEach(item => {
                    item.percentage = ((parseFloat(item.quantity) || 0) / totalQuantity) * 100;
                });
            } else {
                this.currentFormula.ingredients.forEach(item => {
                    item.percentage = 0;
                });
            }
        },
        saveFormula() {
            const payload = {
                ...this.currentFormula, 
                ingredients: this.currentFormula.ingredients.map(ing => ({
                    id: ing.ingredient_id, 
                    quantity: parseFloat(ing.quantity) || 0,
                    unit: ing.unit,
                    percentage: parseFloat(ing.percentage) || 0, 
                    notes: ing.notes
                }))
            };

            let request;
            if (this.formulaModalMode === 'add') {
                request = axios.post('/api/formulas', payload);
            } else {
                request = axios.put(`/api/formulas/${this.currentFormula.id}`, payload);
            }

            request.then(response => {
                alert(response.data.message || 'Formula saved successfully!');
                this.loadFormulas();
                this.closeFormulaModal();
            }).catch(error => {
                alert('Error saving formula: ' + (error.response?.data?.error || error.message));
                console.error('Save formula error:', error.response?.data || error.message, error.response);
            });
        },
        viewFormulaDetails(formula) { 
            axios.get(`/api/formulas/${formula.id}`)
                .then(response => {
                    this.viewedFormula = response.data;
                    const modalElement = document.getElementById('viewFormulaModal');
                    if (modalElement) {
                         this.viewFormulaModalInstance = bootstrap.Modal.getInstance(modalElement) || new bootstrap.Modal(modalElement);
                         this.viewFormulaModalInstance.show();
                    } else {
                        console.error("View formula modal element not found");
                    }
                })
                .catch(error => {
                    alert('Could not load formula details.');
                    console.error('Error fetching formula details:', error);
                });
        },
        closeViewFormulaModal() {
            const modalElement = document.getElementById('viewFormulaModal');
            if (modalElement) {
                const modalInstance = bootstrap.Modal.getInstance(modalElement);
                if (modalInstance) modalInstance.hide();
            }
        },
        confirmDeleteFormula(formulaId) {
            if (confirm('Are you sure you want to delete this formula?')) {
                axios.delete(`/api/formulas/${formulaId}`)
                    .then(response => {
                        alert(response.data.message || 'Formula deleted.');
                        this.loadFormulas();
                    })
                    .catch(error => {
                        alert('Error deleting formula: ' + (error.response?.data?.error || error.message));
                    });
            }
        },
        confirmDuplicateFormula(formulaId) {
            if (confirm('Are you sure you want to duplicate this formula?')) {
                axios.post(`/api/formulas/${formulaId}/duplicate`)
                    .then(response => {
                        alert(response.data.message || 'Formula duplicated.');
                        this.loadFormulas();
                    })
                    .catch(error => {
                        alert('Error duplicating formula: ' + (error.response?.data?.error || error.message));
                    });
            }
        },
        
        // AI Formula Generation Methods
        generateAIFormula() {
            if (!this.aiFormulaUserDescription.trim()) {
                this.aiFormulaError = "Please describe the scent you want to create.";
                return;
            }
            const apiKey = this.getApiKeyForService(this.aiSelectedService);
            if (!apiKey) {
                this.aiFormulaError = `API key for ${this.aiSelectedService} is not set. Please add it in API Key Settings.`;
                return;
            }
             if (!this.aiSelectedModel) {
                this.aiFormulaError = "Please select an AI model for the chosen service.";
                return;
            }

            this.isLoadingAIFormula = true;
            this.aiGeneratedFormulaIngredients = [];
            this.aiFormulaError = '';

            let formulaContext = null;
            if (this.formulaModalMode === 'edit' && this.currentFormula && this.currentFormula.ingredients.length > 0) {
                formulaContext = this.currentFormula.ingredients.map(ing => ({
                    name: this.getIngredientName(ing.ingredient_id), // Get current name from master list
                    quantity: ing.quantity,
                    unit: ing.unit
                })).filter(ing => ing.name && ing.name !== 'Unknown Ingredient'); // Filter out unmapped/unknown
            }

            const payload = {
                user_description: this.aiFormulaUserDescription,
                ai_service: this.aiSelectedService,
                model_id: this.aiSelectedModel,
                api_key: apiKey,
                current_formula_context: formulaContext, // Send current formula if in edit mode
                target_total_quantity: this.aiTargetTotalQuantity ? parseFloat(this.aiTargetTotalQuantity) : null
            };

            axios.post('/api/ai/generate-formula', payload)
                .then(response => {
                    if (response.data.success && response.data.generated_formula) {
                        this.aiGeneratedFormulaIngredients = response.data.generated_formula.map(item => ({
                            ingredient_name_from_ai: item.ingredient_name,
                            ingredient_id: null, 
                            name: item.ingredient_name, 
                            quantity: item.quantity,
                            unit: item.unit,
                            notes: '', 
                            cost_per_unit: 0, 
                            percentage: 0, 
                            is_ai_suggestion: true,
                            used: false, 
                            needs_mapping: false 
                        }));
                        
                        this.aiGeneratedFormulaIngredients.forEach(aiIng => {
                            const matchedInvIng = this.allIngredientsForSelection.find(
                                invIng => invIng.name.toLowerCase() === aiIng.ingredient_name_from_ai.toLowerCase()
                            );
                            if (matchedInvIng) {
                                aiIng.ingredient_id = matchedInvIng.id;
                                aiIng.name = matchedInvIng.name; 
                                aiIng.cost_per_unit = matchedInvIng.cost_per_unit || 0;
                            } else {
                                aiIng.needs_mapping = true;
                            }
                        });

                    } else {
                        this.aiFormulaError = response.data.error || "AI formula generation failed.";
                         if(response.data.raw_ai_response_for_debug){
                            console.warn("AI Raw Response (Generation Failed):", response.data.raw_ai_response_for_debug);
                        }
                    }
                })
                .catch(error => {
                    this.aiFormulaError = error.response?.data?.error || "An error occurred while generating the AI formula.";
                    if(error.response?.data?.raw_ai_response_for_debug){
                        console.warn("AI Raw Response (Catch Block):", error.response.data.raw_ai_response_for_debug);
                    }
                    console.error("AI Formula Generation Error:", error.response);
                })
                .finally(() => {
                    this.isLoadingAIFormula = false;
                });
        },
        useAIGeneratedIngredient(aiIngredient, index) {
            if (!aiIngredient.ingredient_id) {
                alert(`Ingredient "${aiIngredient.ingredient_name_from_ai}" needs to be mapped to an inventory item first or added to inventory.`);
                return;
            }
            
            const existingIndex = this.currentFormula.ingredients.findIndex(ing => ing.ingredient_id === aiIngredient.ingredient_id);

            const newFormulaLine = {
                ingredient_id: aiIngredient.ingredient_id,
                name: aiIngredient.name, 
                quantity: parseFloat(aiIngredient.quantity) || 0,
                unit: aiIngredient.unit,
                notes: aiIngredient.notes || `AI Suggestion: ${aiIngredient.quantity} ${aiIngredient.unit}`,
                cost_per_unit: aiIngredient.cost_per_unit || 0,
                percentage: 0 
            };
            
            if (existingIndex > -1 && confirm(`Ingredient "${aiIngredient.name}" is already in the formula. Update its quantity and unit? (Cancel to add as new line)`)) {
                 this.currentFormula.ingredients[existingIndex].quantity = newFormulaLine.quantity;
                 this.currentFormula.ingredients[existingIndex].unit = newFormulaLine.unit;
                 this.currentFormula.ingredients[existingIndex].notes += (this.currentFormula.ingredients[existingIndex].notes ? "; " : "") + `AI updated: ${newFormulaLine.quantity} ${newFormulaLine.unit}`;
            } else {
                this.currentFormula.ingredients.push(newFormulaLine);
            }
            
            if (index > -1) { 
                this.aiGeneratedFormulaIngredients[index].used = true;
            }
            this.recalculateFormulaPercentages();
        },
        loadAllAIGeneratedIngredients() {
            let notMappedCount = 0;
            this.aiGeneratedFormulaIngredients.forEach((aiIng, idx) => {
                if (aiIng.used) return; 

                if (!aiIng.ingredient_id) {
                    notMappedCount++;
                    return; 
                }
                this.useAIGeneratedIngredient(aiIng, idx); 
            });
            this.aiGeneratedFormulaIngredients.forEach(aiIng => {
                if(aiIng.ingredient_id) aiIng.used = true;
            });


            if (notMappedCount > 0) {
                alert(`${notMappedCount} AI suggested ingredient(s) could not be automatically mapped to your inventory and were skipped. Please review them, map them manually if possible, or add them to your inventory.`);
            }
            this.recalculateFormulaPercentages();
        },
        clearAIGeneratedFormula() {
            this.aiGeneratedFormulaIngredients = [];
            this.aiFormulaError = '';
        }

    }, 
    watch: {
        ingredientCategoryFilter() {
            this.ingredientPagination.page = 1;
            this.loadIngredients();
        },
        ingredientSearch(newValue, oldValue) {
            if (this.searchDebounceTimer) clearTimeout(this.searchDebounceTimer);
            if (newValue !== oldValue || (newValue && (oldValue === undefined || oldValue === null || oldValue === ""))) {
                 this.searchDebounceTimer = setTimeout(() => this.triggerSearch(), 400);
            } else if (!newValue && oldValue) { 
                this.triggerSearch(); 
            }
        },
        'currentFormula.ingredients': {
            handler() {
                this.recalculateFormulaPercentages();
            },
            deep: true 
        },
        formulaSearch(newValue, oldValue) { 
            if (newValue !== oldValue) { 
                this.triggerFormulaSearch();
            }
        },
        currentMainView(newView, oldView) {
            if (newView === 'ingredients') {
                this.$nextTick(() => { 
                    this.initialPerPageAdjustDone = false; 
                    this.adjustPerPageItems();
                });
            }
        },
        aiSelectedService(newService, oldService) {
            if (newService !== oldService) {
                this.aiSelectedModel = ''; // Reset current model
                // Attempt to fetch models for the new service if an API key is available
                const apiKey = this.getApiKeyForService(newService);
                if (apiKey) {
                    this.fetchModelsForService(newService, true); // autoFetch = true
                } else {
                    // If no API key, load fallbacks for the new service
                    this.loadFallbackAIModelsForService(newService);
                }
            }
        },
    } 
});

app.directive('focus', { mounted(el) { el.focus(); } });
app.mount('#app');
