// API URL Base (since we serve from same domain, it's relative)
const API_BASE = '/api';

// Utility for fetching with Auth
async function apiFetch(endpoint, options = {}) {
    const token = localStorage.getItem('token');
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers
    });
    
    if (response.status === 401) {
        // Unauthorized
        logout();
    }
    
    return response;
}

// Global Init
function initApp() {
    const user = JSON.parse(localStorage.getItem('user'));
    const token = localStorage.getItem('token');
    
    // Check auth on protected pages
    if (!token && window.location.pathname !== '/') {
        window.location.href = '/';
        return;
    }

    if (user && document.getElementById('welcomeMsg')) {
        document.getElementById('welcomeMsg').textContent = `Welcome back, ${user.name}!`;
    }
    
    // Admin features visibility
    if (user && user.role === 'Admin' && document.getElementById('newProjectBtn')) {
        document.getElementById('newProjectBtn').style.display = 'inline-block';
    }

    // Logout
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            logout();
        });
    }
}

function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/';
}

// --- Auth Page Logic ---
if (window.location.pathname === '/') {
    const loginCard = document.getElementById('loginCard');
    const registerCard = document.getElementById('registerCard');
    
    document.getElementById('showRegister')?.addEventListener('click', (e) => {
        e.preventDefault();
        loginCard.classList.add('hidden');
        registerCard.classList.remove('hidden');
    });

    document.getElementById('showLogin')?.addEventListener('click', (e) => {
        e.preventDefault();
        registerCard.classList.add('hidden');
        loginCard.classList.remove('hidden');
    });

    // Login Form
    document.getElementById('loginForm')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('loginEmail').value;
        const password = document.getElementById('loginPassword').value;
        const errEl = document.getElementById('loginError');
        errEl.classList.add('hidden');

        try {
            const res = await fetch(`${API_BASE}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });
            const data = await res.json();
            
            if (res.ok) {
                localStorage.setItem('token', data.token);
                localStorage.setItem('user', JSON.stringify(data.user));
                window.location.href = '/dashboard';
            } else {
                errEl.textContent = data.message;
                errEl.classList.remove('hidden');
            }
        } catch (err) {
            errEl.textContent = 'Server error. Please try again.';
            errEl.classList.remove('hidden');
        }
    });

    // Register Form
    document.getElementById('registerForm')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const name = document.getElementById('regName').value;
        const email = document.getElementById('regEmail').value;
        const password = document.getElementById('regPassword').value;
        const role = document.getElementById('regRole').value;
        
        const errEl = document.getElementById('regError');
        const succEl = document.getElementById('regSuccess');
        errEl.classList.add('hidden');
        succEl.classList.add('hidden');

        try {
            const res = await fetch(`${API_BASE}/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, email, password, role })
            });
            const data = await res.json();
            
            if (res.ok) {
                succEl.textContent = 'Registration successful! Please login.';
                succEl.classList.remove('hidden');
                setTimeout(() => {
                    document.getElementById('showLogin').click();
                }, 1500);
            } else {
                errEl.textContent = data.message || data.error;
                errEl.classList.remove('hidden');
            }
        } catch (err) {
            errEl.textContent = 'Server error. Please try again.';
            errEl.classList.remove('hidden');
        }
    });
}

// --- Dashboard Logic ---
async function fetchDashboardStats() {
    if (window.location.pathname !== '/dashboard') return;
    
    try {
        const res = await apiFetch('/dashboard');
        if (!res.ok) return;
        const data = await res.json();
        
        document.getElementById('statProjects').textContent = data.projects_count;
        
        let todo = 0, inProg = 0, done = 0;
        data.task_stats.forEach(stat => {
            if (stat.status === 'To Do') todo = stat.count;
            if (stat.status === 'In Progress') inProg = stat.count;
            if (stat.status === 'Done') done = stat.count;
        });
        
        document.getElementById('statTodo').textContent = todo;
        document.getElementById('statProgress').textContent = inProg;
        document.getElementById('statDone').textContent = done;

        // Render overdue tasks
        const overdueContainer = document.getElementById('overdueTasksContainer');
        overdueContainer.innerHTML = '';
        
        if (data.overdue_tasks.length === 0) {
            overdueContainer.innerHTML = '<div class="list-item text-muted">No overdue tasks. Good job!</div>';
        } else {
            data.overdue_tasks.forEach(task => {
                overdueContainer.innerHTML += `
                    <div class="list-item">
                        <div>
                            <strong>${task.title}</strong>
                            <p class="text-muted" style="font-size: 0.8rem; margin-top: 0.25rem;">Due: ${new Date(task.due_date).toLocaleDateString()}</p>
                        </div>
                        <span class="badge badge-danger">Overdue</span>
                    </div>
                `;
            });
        }
    } catch (e) {
        console.error('Error fetching dashboard stats', e);
    }
}


// --- Project/Task Logic ---
let allUsers = [];

async function fetchProjectsAndTasks() {
    if (window.location.pathname !== '/project') return;
    
    try {
        // Fetch users for assignments
        const uRes = await apiFetch('/users');
        if (uRes.ok) allUsers = await uRes.json();
        
        // Populate assignees dropdown
        const assigneeSelect = document.getElementById('taskAssignee');
        if (assigneeSelect) {
            assigneeSelect.innerHTML = '<option value="">Unassigned</option>';
            allUsers.forEach(u => {
                assigneeSelect.innerHTML += `<option value="${u.id}">${u.name}</option>`;
            });
        }

        // Fetch projects
        const pRes = await apiFetch('/projects');
        const projects = await pRes.json();
        
        const pList = document.getElementById('projectsListContainer');
        const taskProjSelect = document.getElementById('taskProject');
        pList.innerHTML = '';
        if(taskProjSelect) taskProjSelect.innerHTML = '<option value="">Select Project</option>';
        
        if (projects.length === 0) {
            pList.innerHTML = '<div class="list-item text-muted">No projects found.</div>';
        } else {
            projects.forEach(p => {
                pList.innerHTML += `
                    <div class="list-item" style="cursor:pointer;" onclick="filterTasks(${p.id}, '${p.title}')">
                        <strong>${p.title}</strong>
                    </div>
                `;
                if(taskProjSelect) {
                    taskProjSelect.innerHTML += `<option value="${p.id}">${p.title}</option>`;
                }
            });
        }

        // Fetch all tasks initially
        filterTasks(null, 'All Tasks');
        
    } catch (e) {
        console.error(e);
    }
}

async function filterTasks(projectId, title) {
    document.getElementById('currentProjectTitle').textContent = title;
    
    let url = '/tasks';
    if (projectId) url += `?project_id=${projectId}`;
    
    try {
        const res = await apiFetch(url);
        const tasks = await res.json();
        
        const tList = document.getElementById('tasksListContainer');
        tList.innerHTML = '';
        
        if (tasks.length === 0) {
            tList.innerHTML = '<div class="list-item text-muted">No tasks found.</div>';
        } else {
            tasks.forEach(t => {
                let badgeClass = 'badge-todo';
                if (t.status === 'In Progress') badgeClass = 'badge-progress';
                if (t.status === 'Done') badgeClass = 'badge-done';
                
                tList.innerHTML += `
                    <div class="list-item">
                        <div>
                            <strong>${t.title}</strong> ${projectId ? '' : `<span style="font-size:0.8rem; color:var(--text-muted);">(${t.project_title})</span>`}
                            <p class="text-muted" style="font-size: 0.8rem; margin-top: 0.25rem;">
                                Assigned: ${t.assigned_to_name || 'Unassigned'} | Due: ${t.due_date ? new Date(t.due_date).toLocaleDateString() : 'None'}
                            </p>
                        </div>
                        <div style="display:flex; align-items:center; gap: 1rem;">
                            <span class="badge ${badgeClass}">${t.status}</span>
                            <select onchange="updateTaskStatus(${t.id}, this.value)" style="padding: 0.2rem; background: var(--bg-color); color: var(--text-color); border: 1px solid var(--border-color); border-radius: 4px;">
                                <option value="To Do" ${t.status === 'To Do' ? 'selected' : ''}>To Do</option>
                                <option value="In Progress" ${t.status === 'In Progress' ? 'selected' : ''}>In Progress</option>
                                <option value="Done" ${t.status === 'Done' ? 'selected' : ''}>Done</option>
                            </select>
                        </div>
                    </div>
                `;
            });
        }
    } catch (e) {
        console.error(e);
    }
}

async function updateTaskStatus(taskId, status) {
    try {
        const res = await apiFetch(`/tasks/${taskId}`, {
            method: 'PUT',
            body: JSON.stringify({ status })
        });
        if (res.ok) {
            // refresh tasks
            fetchProjectsAndTasks();
        }
    } catch (e) {
        console.error(e);
    }
}

// Modals Setup
if (window.location.pathname === '/project') {
    const projModal = document.getElementById('projectModal');
    const taskModal = document.getElementById('taskModal');

    document.getElementById('newProjectBtn')?.addEventListener('click', () => projModal.classList.add('active'));
    document.getElementById('closeProjectModal')?.addEventListener('click', () => projModal.classList.remove('active'));
    
    document.getElementById('newTaskBtn')?.addEventListener('click', () => taskModal.classList.add('active'));
    document.getElementById('closeTaskModal')?.addEventListener('click', () => taskModal.classList.remove('active'));

    // Create Project
    document.getElementById('projectForm')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const title = document.getElementById('projTitle').value;
        const description = document.getElementById('projDesc').value;
        
        const res = await apiFetch('/projects', {
            method: 'POST',
            body: JSON.stringify({ title, description })
        });
        
        if (res.ok) {
            projModal.classList.remove('active');
            document.getElementById('projectForm').reset();
            fetchProjectsAndTasks();
        } else {
            alert('Error creating project (Admin only)');
        }
    });

    // Create Task
    document.getElementById('taskForm')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const payload = {
            project_id: document.getElementById('taskProject').value,
            title: document.getElementById('taskTitle').value,
            status: document.getElementById('taskStatus').value,
            assigned_to: document.getElementById('taskAssignee').value || null,
            due_date: document.getElementById('taskDate').value || null
        };
        
        const res = await apiFetch('/tasks', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
        
        if (res.ok) {
            taskModal.classList.remove('active');
            document.getElementById('taskForm').reset();
            fetchProjectsAndTasks();
        } else {
            alert('Error creating task');
        }
    });
}
