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
            ingredientPagination: {
                page: 1,
                per_page: 10, // Initial value, will be dynamically adjusted
                total_pages: 1,
                total_items: 0
            },
            currentIngredient: { category_ids: [] }, 
            ingredientModal: { mode: 'add' },       
            viewedIngredient: null,                 
            selectedIngredientIds: [],              
            sortKey: 'name',                        
            sortAsc: true,                          
            editingIngredientId: null, 
            
            searchDebounceTimer: null,
            resizeDebounceTimer: null,
            estimatedRowHeight: 58, // CRITICAL: Tune this based on your actual rendered row height in pixels!
            minPerPage: 5,          // Minimum items to display per page
            initialPerPageAdjustDone: false, // Flag to manage initial adjustment

            newIngredientPanel: {
                name: '', amount: null, unit: 'g', category_ids: [], notes: ''
            },
            categories: [], showAddCategoryForm: false, 
            newCategory: { name: '', description: '', parent_id: null },
            editingCategoryId: null, 
            categoryEditBuffer: { id: null, name: '', description: '', parent_id: null },
            batchCategoriesToApply: [], 
            formulas: [], formulaSearch: '', 
            formulaPagination: { page: 1, per_page: 10, total_pages: 1, total_items: 0 },
            currentFormula: { name: '', creator: '', version: '1.0', description: '', notes: '', ingredients: [] },
            formulaModal: { mode: 'add' }, viewedFormula: null,
            importFile: null, importFileObject: null, rawFileContent: null,
            importAnalysis: { format: '', structure: '', fields: [], item_count: 0, sample_data: [], mapping_suggestion: {}, main_array_key: null, data_path: '', message: '' },
            importMapping: {}, importType: 'ingredients', importStatus: '', importSuccess: false, importErrors: [],
            isAnalyzingFile: false, fileAnalyzedSuccessfully: false, categoryWarnings: [],
            openrouterModels: [], openrouterSystemPrompt: '', openrouterUserPrompt: '', openrouterResponse: '',    
            aiModelOpenRouter: 'openai/gpt-4-turbo', aiPromptOpenRouter: '', aiResponseOpenRouter: '', aiErrorOpenRouter: '',        
            geminiModels: [], geminiSystemPrompt: '', geminiModel: 'gemini-1.5-pro', 
            aiPromptGemini: '', aiResponseGemini: '', aiErrorGemini: '',           
            claudeModels: [], claudeSystemPrompt: '', claudeModel: 'claude-3-opus-20240229', 
            aiPromptClaude: '', aiResponseClaude: '', aiErrorClaude: '',           
            apiSettings: { openrouter: '', gemini: '', claude: '' },
            apiSettingsSaved: false, apiSettingsError: '', rememberApiKeys: true,
            currentApiService: '', currentApiKey: '', showCurrentApiKey: false, rememberCurrentApiKey: true, 
            savedPrompts: [], newPromptName: '', currentPromptService: '', 
            showContextualAIPanel: false, contextualAIItem: null, 
            lastUpdatedTimestamp: new Date().toISOString(),
            resizing: false, resizingColumn: null, startX: 0, startWidth: 0
        };
    }, // IMPORTANT: Comma after data()
    computed: {
        pageNumbers() { 
            const pages = []; const maxPagesToShow = 5; const currentPage = this.ingredientPagination.page; const totalPages = this.ingredientPagination.total_pages;
            if (totalPages <= 1) return [];
            if (totalPages <= maxPagesToShow) { for (let i = 1; i <= totalPages; i++) pages.push(i); } 
            else { let startPage = Math.max(1, currentPage - Math.floor(maxPagesToShow / 2)); let endPage = Math.min(totalPages, startPage + maxPagesToShow - 1); if (endPage - startPage + 1 < maxPagesToShow) startPage = Math.max(1, endPage - maxPagesToShow + 1); for (let i = startPage; i <= endPage; i++) pages.push(i); }
            return pages;
        },
        formulaPageNumbers() { 
            const pages = []; const maxPages = 5; const totalPages = this.formulaPagination.total_pages; const currentPage = this.formulaPagination.page;
            if (totalPages <= 1) return [];
            if (totalPages <= maxPages) { for (let i = 1; i <= totalPages; i++) pages.push(i); } 
            else { let startPage = Math.max(1, currentPage - Math.floor(maxPages / 2)); let endPage = Math.min(totalPages, startPage + maxPages - 1); if (endPage - startPage + 1 < maxPages) startPage = Math.max(1, endPage - maxPages + 1); for (let i = startPage; i <= endPage; i++) pages.push(i); }
            return pages;
        },
        rootCategories() { 
            if (!this.categories) return [];
            return this.categories.filter(c => !c.parent_id).map(rc => ({ ...rc, subcategories: this.categories.filter(sub => sub.parent_id === rc.id) }));
        },
        ingredientsForFormula() { return this.ingredients.map(ing => ({ id: ing.id, name: ing.name, unit_of_measurement: ing.unit_of_measurement, cost_per_unit: ing.cost_per_unit })); },
        calculatedFormulaTotalCost() { 
            if (!this.currentFormula || !this.currentFormula.ingredients) return 0;
            return this.currentFormula.ingredients.reduce((total, item) => { const cost = parseFloat(item.cost_per_unit) || 0; const quantity = parseFloat(item.quantity) || 0; return total + (cost * quantity); }, 0);
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
                    valA = a.categories && a.categories.length > 0 ? a.categories.map(c=>c.name).join(',').toLowerCase() : '';
                    valB = b.categories && b.categories.length > 0 ? b.categories.map(c=>c.name).join(',').toLowerCase() : '';
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
        }
    }, // IMPORTANT: Comma after computed
    mounted() { 
        this.initializeDarkMode(); 
        this.loadInitialData(); 
        this.setupEventListeners(); 
        window.addEventListener('resize', this.handleWindowResize);
        this.loadApiSettings(); 
        this.loadDefaultPrompts(); 
        this.loadSavedPrompts(); 
    }, // IMPORTANT: Comma after mounted
    beforeUnmount() {
        window.removeEventListener('resize', this.handleWindowResize);
        if (this.resizeDebounceTimer) clearTimeout(this.resizeDebounceTimer);
        if (this.searchDebounceTimer) clearTimeout(this.searchDebounceTimer);
    }, // IMPORTANT: Comma after beforeUnmount
    methods: {
        // --- DARK MODE METHODS START ---
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
        // --- DARK MODE METHODS END ---

        loadInitialData() { this.loadIngredients(); this.loadCategories(); this.loadAIModels(); },
        triggerSearch() { this.ingredientPagination.page = 1; if (this.searchDebounceTimer) { clearTimeout(this.searchDebounceTimer); this.searchDebounceTimer = null; } this.loadIngredients(); },
        loadIngredients() {
            if (this.searchDebounceTimer) { clearTimeout(this.searchDebounceTimer); this.searchDebounceTimer = null; }
            const params = { page: this.ingredientPagination.page, per_page: this.ingredientPagination.per_page, sort_by: this.sortKey, sort_direction: this.sortAsc ? 'asc' : 'desc' };
            const searchTermTrimmed = this.ingredientSearch ? this.ingredientSearch.trim() : '';
            if (searchTermTrimmed) params.search = searchTermTrimmed;
            if (this.ingredientCategoryFilter) params.category_id = this.ingredientCategoryFilter;
            axios.get('/api/ingredients', { params })
            .then(response => {
                this.ingredients = response.data.items.map(ing => ({ ...ing, isEditing: false, isEditingAmount: false, editBuffer: {} }));
                this.ingredientPagination = response.data.pagination; this.lastUpdatedTimestamp = new Date().toISOString(); 
                if (!this.initialPerPageAdjustDone) { this.$nextTick(() => { this.adjustPerPageItems(); }); }
            })
            .catch(error => { console.error('Error loading ingredients:', error.response?.data || error.message || error); this.ingredients = []; this.ingredientPagination = { page: 1, per_page: this.minPerPage, total_pages: 0, total_items: 0 }; });
        },
        async getElementHeight(selector) { await this.$nextTick(); const e = document.querySelector(selector); return e ? e.offsetHeight : 0; },
        async adjustPerPageItems() {
            await this.$nextTick(); const mc = document.querySelector('.main-content'); if (!mc) {console.warn("'.main-content' not found for per-page adjustment."); return;}
            const mcs = window.getComputedStyle(mc); const padT = parseFloat(mcs.paddingTop)||0; const padB = parseFloat(mcs.paddingBottom)||0;
            const mchH = await this.getElementHeight('.main-content .main-content-header');
            const tthH = await this.getElementHeight('.main-content .resizable-table thead.sticky-thead');
            const pgnH = await this.getElementHeight('.main-content nav[aria-label="Ingredient pagination"]');
            const bBuf = 10; const cbH = mc.clientHeight - padT - padB;
            const avH = cbH - mchH - tthH - pgnH - bBuf;
            if (avH > 0 && this.estimatedRowHeight > 0) {
                let npp = Math.floor(avH / this.estimatedRowHeight); npp = Math.max(this.minPerPage, npp);
                const ppc = npp !== this.ingredientPagination.per_page;
                if (ppc || !this.initialPerPageAdjustDone) {
                    const pact = this.ingredientPagination.page !== 1 || !this.initialPerPageAdjustDone;
                    this.ingredientPagination.per_page = npp;
                    if (ppc || pact ) this.ingredientPagination.page = 1; 
                    this.initialPerPageAdjustDone = true; this.loadIngredients();
                }
            } else { if (!this.initialPerPageAdjustDone) { this.ingredientPagination.per_page = Math.max(this.ingredientPagination.per_page,this.minPerPage); this.initialPerPageAdjustDone = true; if(this.ingredients.length===0 && this.ingredientPagination.total_items===0) this.loadIngredients(); } else if (this.ingredientPagination.per_page < this.minPerPage) { this.ingredientPagination.per_page = this.minPerPage; if(this.ingredientPagination.page !== 1) this.ingredientPagination.page = 1; this.loadIngredients();}}
        },
        handleWindowResize() { if (this.resizeDebounceTimer) clearTimeout(this.resizeDebounceTimer); this.resizeDebounceTimer = setTimeout(() => this.adjustPerPageItems(), 300); },
        changePage(p) { if (p >= 1 && p <= this.ingredientPagination.total_pages && p !== this.ingredientPagination.page) { this.ingredientPagination.page = p; this.loadIngredients(); } },
        sortIngredients(k) { if (this.sortKey === k) this.sortAsc = !this.sortAsc; else { this.sortKey = k; this.sortAsc = true; } this.ingredientPagination.page = 1; this.loadIngredients(); },
        getSortIcon(k) { if (this.sortKey !== k) return 'bi-arrow-down-up text-muted'; return this.sortAsc ? 'bi-sort-up-alt' : 'bi-sort-down'; },
        clearFiltersAndSort() { this.ingredientSearch = ''; this.ingredientCategoryFilter = ''; this.sortKey = 'name'; this.sortAsc = true; this.triggerSearch(); },
        addIngredientFromPanel() { if (!this.newIngredientPanel.name.trim()) { alert('Name required.'); return; } if (this.newIngredientPanel.category_ids.length > 3) { alert('Max 3 cats.'); return; } const p = { name: this.newIngredientPanel.name, stock_quantity: this.newIngredientPanel.amount, unit_of_measurement: this.newIngredientPanel.unit, category_ids: this.newIngredientPanel.category_ids, notes: this.newIngredientPanel.notes, description:'', supplier:'', cost_per_unit:null}; axios.post('/api/ingredients',p).then(r=>{this.loadIngredients(); this.newIngredientPanel={name:'',amount:null,unit:'g',category_ids:[],notes:''}; alert(r.data.message||'Added!');}).catch(e=>alert('Failed: '+(e.response?.data?.error||e.message))); },
        startEditing(ing) { if (this.editingIngredientId !== null && this.editingIngredientId !== ing.id) { const cur = this.ingredients.find(i=>i.id===this.editingIngredientId); if(cur)this.cancelEditing(cur,true); } this.editingIngredientId=ing.id; ing.editBuffer=JSON.parse(JSON.stringify(ing)); ing.editBuffer.category_ids=ing.categories?ing.categories.map(c=>c.id):[]; ing.isEditing=true; ing.isEditingAmount=false; this.$nextTick(()=>{const el=document.querySelector(`#ingredient-row-${ing.id} input[type='text'], #ingredient-row-${ing.id} select, #ingredient-row-${ing.id} textarea`); if(el)el.focus();}); },
        startEditingAmount(ing) { if (this.editingIngredientId !== null && this.editingIngredientId !== ing.id) { const cur = this.ingredients.find(i=>i.id===this.editingIngredientId); if(cur)this.cancelEditing(cur,true); } this.editingIngredientId=ing.id; ing.editBuffer=JSON.parse(JSON.stringify(ing)); ing.isEditing=false; ing.isEditingAmount=true; this.$nextTick(()=>{const el=document.querySelector(`#ingredient-row-${ing.id} input[type='number']`); if(el)el.focus();}); },
        saveInlineEdit(ing) { if(!ing||!ing.editBuffer)return; if(ing.isEditing&&(!ing.editBuffer.name||ing.editBuffer.name.trim()==='')){alert("Name required.");return;} const nf=['cost_per_unit','stock_quantity','minimum_stock_threshold']; for(const f of nf){if(ing.editBuffer[f]!==null&&String(ing.editBuffer[f]).trim()!==''){let vs=String(ing.editBuffer[f]).replace(/[^0-9.-]+/g,""); if(vs===''||isNaN(parseFloat(vs))){alert(`Invalid ${f}.`);return;} ing.editBuffer[f]=parseFloat(vs);}else if(String(ing.editBuffer[f]).trim()==='')ing.editBuffer[f]=null;} const p={...ing.editBuffer}; if(ing.isEditing)p.category_ids=ing.editBuffer.category_ids||(ing.categories?ing.categories.map(c=>c.id):[]); delete p.isEditing; delete p.isEditingAmount; delete p.categories; delete p.editBuffer; axios.put(`/api/ingredients/${ing.id}`,p).then(r=>{const uD=r.data.ingredient||r.data; const idx=this.ingredients.findIndex(i=>i.id===ing.id); if(idx!==-1){Object.assign(this.ingredients[idx],uD); this.ingredients[idx].isEditing=false; this.ingredients[idx].isEditingAmount=false; this.ingredients[idx].editBuffer={};}else this.loadIngredients(); this.editingIngredientId=null; alert(r.data.message||'Updated!');}).catch(e=>alert('Save failed: '+(e.response?.data?.error||e.message))); },
        cancelEditing(ing,auto=false){if(ing){ing.isEditing=false;ing.isEditingAmount=false;ing.editBuffer={};} if(this.editingIngredientId===ing.id||auto)this.editingIngredientId=null;},
        displayAmountAndUnit(ing){const q=ing.stock_quantity;const u=ing.unit_of_measurement;const su=['g','mL','oz','drops'];let qd=(q!==null&&typeof q!=='undefined')?q:"N/A";if(u&&typeof u==='string'){const ul=u.toLowerCase();if(su.includes(u))return`${qd}${u}`;if(ul.includes("not specified"))return`Size not Specified (Amount ${qd}?)`;if(q===1||qd==="N/A")return`<span class="unit-value">${u}</span>`;return`<span class="amount-value">${qd}</span> <span class="times-symbol">&times;</span> <span class="unit-value">${u}</span>`;}if(qd!=="N/A")return`<span class="amount-value">${qd}</span>`;return`<span class="amount-value">N/A</span>`;},
        formatNotes(n){if(n===null||typeof n==='undefined'||(typeof n==='string'&&n.trim()===''))return'';if(typeof n==='string'){if(n.trim()==="[]")return'';if(n.startsWith("['")&&n.endsWith("']")){try{const j=n.replace(/'/g,'"');const p=JSON.parse(j);if(Array.isArray(p)){if(p.length===0)return'';return p.join(', ');}}catch(e){let cl=n.substring(2,n.length-2).replace(/',\s*'/g,', ');if(cl.trim()==='')return'';return cl;}}}return String(n);},
        deleteIngredient(id) { if(confirm('Delete?')) axios.delete(`/api/ingredients/${id}`).then(()=>{this.loadIngredients();alert('Deleted.')}).catch(e=>alert('Failed: '+(e.response?.data?.error||e.message))); },
        toggleSelectAllIngredients(event) { this.selectedIngredientIds = event.target.checked ? this.sortedIngredients.map(ing => ing.id) : []; },
        promptDeleteSelectedIngredients() { if (!this.selectedIngredientIds.length) { alert("None selected."); return; } if (confirm(`Delete ${this.selectedIngredientIds.length} items?`)) this.deleteSelectedIngredients(); },
        deleteSelectedIngredients() { axios.post('/api/ingredients/delete-selected', { ids: this.selectedIngredientIds }).then(res => { alert(res.data.message); this.selectedIngredientIds = []; this.loadIngredients(); }).catch(e => alert('Failed: ' + (e.response?.data?.error || e.message))); },
        promptDeleteAllIngredients() { if (!this.ingredients.length) { alert("No items to delete."); return; } if (confirm('DELETE ALL ingredients? Irreversible.')) if (confirm('Confirm permanent deletion of ALL items?')) this.deleteAllIngredients(); },
        deleteAllIngredients() { axios.delete('/api/ingredients/all').then(res => { alert(res.data.message); this.loadIngredients(); this.selectedIngredientIds = []; }).catch(e => alert('Failed: ' + (e.response?.data?.error || e.message))); },
        viewIngredient(id) { const ing = this.ingredients.find(i => i.id === id); if (ing) { if (this.editingIngredientId) this.cancelEditing(this.ingredients.find(i=>i.id===this.editingIngredientId), true); this.viewedIngredient = { ...ing }; new bootstrap.Modal(document.getElementById('viewIngredientModal')).show(); } },
        loadCategories() { axios.get('/api/categories').then(res => this.categories = res.data).catch(e => console.error('Load categories error:', e)); },
        navigateToManageCategories() { this.loadCategories(); this.editingCategoryId = null; this.showAddCategoryForm = false; this.newCategory = { name: '', description: '', parent_id: null }; const el = document.getElementById('manageCategoriesModal'); if (el) new bootstrap.Modal(el).show(); else alert("Category modal UI not found."); },
        showAddCategoryInlineForm() { this.cancelCategoryEdit(); this.newCategory = { name: '', description: '', parent_id: null }; this.showAddCategoryForm = true; this.$nextTick(() => document.getElementById('newCatName')?.focus()); },
        cancelAddCategoryInline() { this.showAddCategoryForm = false; this.newCategory = { name: '', description: '', parent_id: null }; },
        saveNewInlineCategory() { if (!this.newCategory.name.trim()) { alert('Category name needed.'); return; } axios.post('/api/categories', this.newCategory).then(res => { alert(res.data.message); this.loadCategories(); this.cancelAddCategoryInline(); }).catch(e => alert('Failed: ' + (e.response?.data?.error || e.message))); },
        startCategoryEdit(cat) { this.cancelAddCategoryInline(); this.editingCategoryId = cat.id; this.categoryEditBuffer = JSON.parse(JSON.stringify(cat)); if (!this.categoryEditBuffer.parent_id) this.categoryEditBuffer.parent_id = null; },
        cancelCategoryEdit() { this.editingCategoryId = null; this.categoryEditBuffer = { id: null, name: '', description: '', parent_id: null }; },
        saveCategoryEdit() { if (!this.categoryEditBuffer.name.trim()) { alert('Category name needed.'); return; } if (this.categoryEditBuffer.id === this.categoryEditBuffer.parent_id && this.categoryEditBuffer.parent_id !== null) { alert('Cannot be own parent.'); return; } const payload = { name: this.categoryEditBuffer.name, description: this.categoryEditBuffer.description, parent_id: this.categoryEditBuffer.parent_id }; axios.put(`/api/categories/${this.editingCategoryId}`, payload).then(res => { alert(res.data.message); this.loadCategories(); this.cancelCategoryEdit(); }).catch(e => alert('Failed: ' + (e.response?.data?.error || e.message))); },
        confirmDeleteCategory(id) { const cat = this.categories.find(c => c.id === id); if (!cat) return; if (cat.ingredient_count > 0) { alert(`Cannot delete "${cat.name}": ${cat.ingredient_count} ingredients assigned.`); return; } if (confirm(`Delete category "${cat.name}"?`)) this.deleteCategory(id); },
        deleteCategory(id) { axios.delete(`/api/categories/${id}`).then(res => { alert(res.data.message); this.loadCategories(); this.loadIngredients(); }).catch(e => alert('Failed: ' + (e.response?.data?.error || e.message))); },
        getCategoryNameById(id) { if (!id) return ''; const cat = this.categories.find(c => c.id === id); return cat ? cat.name : 'Unknown'; },
        promptResetCategoriesToDefaults() { if (confirm('RESET ALL CATEGORIES TO DEFAULTS? Deletes current categories and unassigns items.')) if (confirm('Confirm IRREVERSIBLE category data reset?')) axios.post('/api/categories/reset-to-defaults').then(res => { alert(res.data.message); this.loadCategories(); this.loadIngredients(); }).catch(e => alert('Failed: ' + (e.response?.data?.error || e.message))); },
        navigateToImportData() { this.importFile=null; this.importFileObject=null; this.rawFileContent=null; this.importAnalysis={format:'',structure:'',fields:[],item_count:0,sample_data:[],mapping_suggestion:{},main_array_key:null,message:'',data_path:''}; this.importMapping={}; this.importStatus=''; this.importSuccess=false; this.importErrors=[]; this.categoryWarnings=[]; this.isAnalyzingFile=false; this.fileAnalyzedSuccessfully=false; const fi=document.getElementById('importFileModal'); if(fi)fi.value=''; const modal=document.getElementById('importDataModal'); if(modal)new bootstrap.Modal(modal).show(); else alert("Import UI error."); },
        exportData(format) { if(format==='json'){if(!this.ingredients.length){alert("Nothing to export.");return;} const str="data:text/json;charset=utf-8,"+encodeURIComponent(JSON.stringify(this.ingredients,null,2)); const a=document.createElement('a');a.href=str;a.download="ingredients.json";document.body.appendChild(a);a.click();document.body.removeChild(a);alert("Exported as JSON.");}else if(format==='csv')alert("CSV export: backend recommended.");},
        handleFileUpload(event){this.importFile=event.target.files[0];this.importFileObject=this.importFile;this.importAnalysis={format:'',structure:'',fields:[],item_count:0,sample_data:[],mapping_suggestion:{},main_array_key:null,message:'',data_path:''};this.importMapping={};this.importStatus='';this.importErrors=[];this.categoryWarnings=[];this.fileAnalyzedSuccessfully=false;if(this.importFile){const r=new FileReader();r.onload=e=>{this.rawFileContent=e.target.result;this.analyzeFile();};r.onerror=e=>{this.importStatus="Error reading file.";this.importErrors=["Could not read file."];};r.readAsText(this.importFile);}},
        analyzeFile(){if(!this.importFile){this.importStatus='Select file.';return;}this.isAnalyzingFile=true;this.importStatus='Analyzing...';this.importErrors=[];this.categoryWarnings=[];this.fileAnalyzedSuccessfully=false;this.importAnalysis={format:'',structure:'',fields:[],item_count:0,sample_data:[],mapping_suggestion:{},main_array_key:null,message:'',data_path:''};this.importMapping={};const fd=new FormData();fd.append('file',this.importFile);axios.post('/api/import/analyze',fd,{headers:{'Content-Type':'multipart/form-data'}}).then(res=>{if(res.data&&res.data.fields!==undefined&&Array.isArray(res.data.fields)&&res.data.sample_data!==undefined&&Array.isArray(res.data.sample_data)){this.importAnalysis=res.data;this.importStatus=`Analyzed: ${this.importAnalysis.item_count||0} items.`;this.fileAnalyzedSuccessfully=true;this.importMapping={...(this.importAnalysis.mapping_suggestion||{})};}else{const err=res.data?.error||res.data?.message||'Analysis incomplete.';this.importStatus='Error: Incomplete data.';this.importErrors=[err];this.fileAnalyzedSuccessfully=false;}}).catch(e=>{let err='Unknown analysis error.';if(e.response?.data?.error)err=e.response.data.error;else if(typeof e.response?.data==='string')err=e.response.data;else if(e.message)err=e.message;this.importStatus='Error analyzing.';this.importErrors=[err];this.fileAnalyzedSuccessfully=false;}).finally(()=>this.isAnalyzingFile=false);},
        processImport(){if(!this.importAnalysis||!this.rawFileContent||!this.fileAnalyzedSuccessfully){this.importStatus='Analyze file first.';return;}this.importStatus='Processing...';this.importErrors=[];this.categoryWarnings=[];this.importSuccess=false;const p={mapping:this.importMapping,import_type:this.importType,format:this.importAnalysis.format,raw_file_content:this.rawFileContent,main_array_key:this.importAnalysis.main_array_key};axios.post('/api/import/process',p).then(res=>{this.importStatus=res.data.message||'Import complete.';this.importSuccess=res.data.success||false;this.importErrors=res.data.errors||[];this.categoryWarnings=res.data.category_warnings||[];if(res.data.imported_count>0)this.loadIngredients();}).catch(e=>{this.importStatus='Error processing.';this.importErrors=[e.response?.data?.error||'Unknown import error.'];this.importSuccess=false;});},
        formatFieldName(f){if(!f)return'';return f.replace(/_/g,' ').replace(/\b\w/g,l=>l.toUpperCase());},
        batchUpdateNotes(){if(!this.selectedIngredientIds.length){alert("None selected.");return;}const n=prompt(`Notes for ${this.selectedIngredientIds.length} items:`);if(n!==null)axios.post('/api/ingredients/batch-update',{ids:this.selectedIngredientIds,notes:n}).then(r=>{alert(r.data.message);this.loadIngredients();this.selectedIngredientIds=[];}).catch(e=>alert('Failed: '+(e.response?.data?.error||e.message)));},
        batchUpdateCategories(){if(!this.selectedIngredientIds.length){alert("None selected.");return;}this.batchCategoriesToApply=[];const m=document.getElementById('batchCategoryModal');if(m)new bootstrap.Modal(m).show();else alert("Batch category UI error.");},
        applyBatchCategoryUpdate(){if(!this.selectedIngredientIds.length){this.closeModal('batchCategoryModal');return;}axios.post('/api/ingredients/batch-update',{ids:this.selectedIngredientIds,category_ids:this.batchCategoriesToApply}).then(r=>{alert(r.data.message);this.loadIngredients();this.selectedIngredientIds=[];this.closeModal('batchCategoryModal');}).catch(e=>{alert('Failed: '+(e.response?.data?.error||e.message));this.closeModal('batchCategoryModal');});},
        toggleGlobalAIChat(){const m=document.getElementById('globalAiChatModal');if(m)new bootstrap.Modal(m).show();else alert("AI Chat modal not found.");},
        showAIContextPanel(type,id){if(type==='ingredient')this.contextualAIItem=this.ingredients.find(i=>i.id===id);if(this.contextualAIItem)this.showContextualAIPanel=true;},
        hideAIContextPanel(){this.showContextualAIPanel=false;this.contextualAIItem=null;},
        loadAIModels(){axios.get('/api/ai/models').then(r=>{this.openrouterModels=r.data.openrouter||[];this.geminiModels=r.data.gemini||[];this.claudeModels=r.data.claude||[];if(this.openrouterModels.length&&!this.aiModelOpenRouter)this.aiModelOpenRouter=this.openrouterModels[0].id;if(this.geminiModels.length&&!this.geminiModel)this.geminiModel=this.geminiModels[0].id;if(this.claudeModels.length&&!this.claudeModel)this.claudeModel=this.claudeModels[0].id;}).catch(e=>console.error('Error loading AI models:',e));},
        loadDefaultPrompts(){axios.get('/api/ai/default-prompts').then(r=>{this.openrouterSystemPrompt=r.data.openrouter||'';this.geminiSystemPrompt=r.data.gemini||'';this.claudeSystemPrompt=r.data.claude||'';}).catch(e=>console.error("Error loading default prompts",e));},
        resetSystemPrompt(s){axios.get('/api/ai/default-prompts').then(r=>{if(s==='openrouter')this.openrouterSystemPrompt=r.data.openrouter||'';else if(s==='gemini')this.geminiSystemPrompt=r.data.gemini||'';else if(s==='claude')this.claudeSystemPrompt=r.data.claude||'';}).catch(e=>console.error("Error resetting prompt",e));},
        generateAIResponse(s){alert(`Generate AI for ${s}: Needs API key & call.`);},
        loadSavedPrompts(){axios.get('/api/ai/saved-prompts').then(r=>this.savedPrompts=r.data||[]).catch(e=>console.error("Error loading saved prompts",e));},
        loadSavedPrompt(p){if(!p)return;if(p.service==='openrouter'){this.aiModelOpenRouter=p.model;this.openrouterSystemPrompt=p.system_prompt;this.aiPromptOpenRouter=p.user_prompt;}alert(`Loaded: ${p.name}`);},
        saveCurrentPrompt(s){this.currentPromptService=s;this.newPromptName='';alert("Save Prompt: Needs modal.");},
        confirmSavePrompt(){alert("Confirm Save: Needs impl.");},
        showApiKeyModal(s){this.currentApiService=s;this.currentApiKey=this.getApiKey(s)||'';alert(`API Key Modal for ${s}: Needs modal.`);},
        saveCurrentApiKey(){alert("Save API Key: Needs impl.");},
        saveApiSettings(){alert("Save API Settings: Needs impl.");},
        saveApiSettingsToStorage(){},loadApiSettings(){},getApiKey(s){return'';},
        setupEventListeners() { document.addEventListener('mousemove', this.handleMouseMove); document.addEventListener('mouseup', this.handleMouseUp); }, 
        startResize(e,idx){this.resizing=true;this.resizingColumn=e.target.closest('th');this.startX=e.pageX;this.startWidth=this.resizingColumn.offsetWidth;e.preventDefault();},
        handleMouseMove(e){if(!this.resizing||!this.resizingColumn)return;const dX=e.pageX-this.startX;constnW=this.startWidth+dX;if(nW>50)this.resizingColumn.style.width=`${nW}px`;}, 
        handleMouseUp(){if(this.resizing){this.resizing=false;this.resizingColumn=null;}},
        formatCurrency(v){if(v===null||typeof v==='undefined'||String(v).trim()==='')return'';return new Intl.NumberFormat('en-US',{style:'currency',currency:'USD'}).format(parseFloat(v));}, 
        formatDate(d){if(!d)return'N/A';try{const o={year:'numeric',month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'};return new Date(d).toLocaleDateString(undefined,o);}catch(e){return d;}},
        closeModal(id){const el=document.getElementById(id);if(el){const i=bootstrap.Modal.getInstance(el);if(i)i.hide();else try{new bootstrap.Modal(el).hide();}catch(e){console.warn("Could not hide modal:",id,e);}}else console.warn("Modal not found:",id);},
        getIngredientName(id){const i=this.ingredients.find(ing=>ing.id===id);return i?i.name:'Unknown';}
    }, // IMPORTANT: Comma after methods
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
        }
    } // No comma after last property (watch)
});

app.directive('focus', { mounted(el) { el.focus(); } });
app.mount('#app');