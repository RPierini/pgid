const demoUsers = [
  { username: "alice", label: "Alice - Aluna" },
  { username: "bob", label: "Bob - Professor" },
  { username: "carlos", label: "Carlos - Coordenador" },
];

const topologyNodes = [
  "Cliente / App",
  "API Gateway (PEP)",
  "IdP / PDP",
  "Policy Admin / PAP",
  "Identity DB / PIP",
  "Backend API",
  "Business DB",
  "Object Storage",
];

function decodeBase64Url(value) {
  if (!value) return "";
  const normalized = value.replace(/-/g, "+").replace(/_/g, "/");
  const padding = "=".repeat((4 - (normalized.length % 4 || 4)) % 4);
  return atob(normalized + padding);
}

function encodeBase64Url(value) {
  return btoa(unescape(encodeURIComponent(value)))
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/g, "");
}

document.addEventListener("alpine:init", () => {
  Alpine.data("gidDemo", () => ({
    users: demoUsers,
    selectedUser: "alice",
    token: "",
    forgedToken: "",
    useForgedToken: false,
    jwtHeader: "",
    jwtPayload: "",
    jwtSignature: "",
    attackPayload: "",
    logs: [],
    lastResponse: null,
    lastDownload: null,
    activeNodes: {},
    flowSteps: [],
    flowStepIndex: -1,
    pending: false,
    showLoginModal: false,
    loginPassword: "",

    init() {
      this.resetTopology();
    },

    resetTopology() {
      this.activeNodes = topologyNodes.reduce((acc, node) => {
        acc[node] = { active: false, status: null, detail: "" };
        return acc;
      }, {});
      this.flowSteps = [];
      this.flowStepIndex = -1;
    },

    nodeClasses(node) {
      const entry = this.activeNodes[node];
      if (!entry || !entry.active) {
        return "border-slate-700 bg-slate-900/70 text-slate-300";
      }
      if (entry.status >= 400) {
        return "border-rose-400 bg-rose-500/20 text-rose-100 shadow-lg shadow-rose-500/20";
      }
      return "border-emerald-400 bg-emerald-500/20 text-emerald-100 shadow-lg shadow-emerald-500/20";
    },

    statusBadge(node) {
      const entry = this.activeNodes[node];
      return entry && entry.status ? `HTTP ${entry.status}` : "idle";
    },

    currentToken() {
      if (this.useForgedToken && this.forgedToken) {
        return this.forgedToken;
      }
      return this.token;
    },

    decodeToken(token) {
      const parts = token.split(".");
      if (parts.length !== 3) {
        throw new Error("JWT inválido.");
      }
      return {
        header: JSON.parse(decodeBase64Url(parts[0])),
        payload: JSON.parse(decodeBase64Url(parts[1])),
        signature: parts[2],
      };
    },

    syncInspector(token) {
      if (!token) {
        this.jwtHeader = "";
        this.jwtPayload = "";
        this.jwtSignature = "";
        this.attackPayload = "";
        return;
      }
      const decoded = this.decodeToken(token);
      this.jwtHeader = JSON.stringify(decoded.header, null, 2);
      this.jwtPayload = JSON.stringify(decoded.payload, null, 2);
      this.jwtSignature = decoded.signature;
      this.attackPayload = JSON.stringify(decoded.payload, null, 2);
    },

    forgeToken() {
      if (!this.token) {
        this.addLog("LAB", "local", 400, 0, "Faça login antes de forjar o token.");
        return;
      }
      try {
        const parts = this.token.split(".");
        const forgedPayload = JSON.stringify(JSON.parse(this.attackPayload));
        const encodedPayload = encodeBase64Url(forgedPayload);
        this.forgedToken = `${parts[0]}.${encodedPayload}.${parts[2]}`;
        this.useForgedToken = true;
        this.jwtPayload = JSON.stringify(JSON.parse(this.attackPayload), null, 2);
        this.addLog("LAB", "token-forjado", 200, 0, "Payload alterado sem nova assinatura.");
      } catch (error) {
        this.addLog("LAB", "token-forjado", 400, 0, error.message);
      }
    },

    logout() {
      this.token = "";
      this.forgedToken = "";
      this.useForgedToken = false;
      this.lastResponse = null;
      this.lastDownload = null;
      this.syncInspector("");
      this.resetTopology();
      this.addLog("POST", "/logout", 200, 0, "Sessão local encerrada.");
    },

    isLoggedIn() {
      return !!this.token;
    },

    currentUserName() {
      const u = this.users.find((user) => user.username === this.selectedUser);
      return u ? u.label : this.selectedUser;
    },

    openLoginModal() {
      this.loginPassword = "";
      this.showLoginModal = true;
    },

    closeLoginModal() {
      this.showLoginModal = false;
      this.loginPassword = "";
    },

    async login() {
      this.closeLoginModal();
      await this.runRequest({
        method: "POST",
        endpoint: "/auth/login",
        body: { username: this.selectedUser },
        includeAuth: false,
        onSuccess: (result) => {
          this.token = result.access_token;
          this.forgedToken = "";
          this.useForgedToken = false;
          this.syncInspector(result.access_token);
          this.lastResponse = result;
          this.addLog("AUTH", "/auth/login", 200, result?.flow?.length || 0, `Login de ${result.user?.label ?? this.selectedUser} (senha aceita para demonstração).`);
        },
      });
    },

    async triggerAction(action) {
      const actions = {
        notas: {
          method: "GET",
          endpoint: "/api/aluno/notas",
        },
        lancar: {
          method: "POST",
          endpoint: "/api/professor/lancar-notas",
          body: {
            disciplina: "Arquitetura de Software",
            aluno: "alice",
            nota: 9.7,
          },
        },
        trancar: {
          method: "DELETE",
          endpoint: "/api/coordenador/trancar-curso",
          body: {
            curso: "Engenharia de Software",
            motivo: "Ajuste operacional do semestre",
          },
        },
        storage: {
          method: "GET",
          endpoint: "/api/storage/presigned-url",
          afterSuccess: async (result) => {
            this.lastDownload = await this.downloadFromStorage(result.data.download_url);
          },
        },
      };
      await this.runRequest(actions[action]);
    },

    async runRequest(config) {
      const startedAt = performance.now();
      this.pending = true;
      try {
        const headers = { "Content-Type": "application/json" };
        if (config.includeAuth !== false && this.currentToken()) {
          headers.Authorization = "Bearer " + this.currentToken();
        }

        const response = await fetch(config.endpoint, {
          method: config.method,
          headers,
          body: config.body ? JSON.stringify(config.body) : undefined,
        });
        const result = await response.json();
        const duration = Math.round(performance.now() - startedAt);
        await this.animateFlow(result.flow || []);
        this.lastResponse = result;
        this.addLog(config.method, config.endpoint, response.status, duration, result.message);
        if (!response.ok) {
          return;
        }
        if (config.onSuccess) {
          config.onSuccess(result);
        }
        if (config.afterSuccess) {
          await config.afterSuccess(result);
        }
      } catch (error) {
        const duration = Math.round(performance.now() - startedAt);
        this.addLog(config.method, config.endpoint, 500, duration, error.message);
      } finally {
        this.pending = false;
      }
    },

    async downloadFromStorage(url) {
      const startedAt = performance.now();
      const response = await fetch(url);
      const result = await response.json();
      const duration = Math.round(performance.now() - startedAt);
      await this.animateFlow(result.flow || []);
      this.addLog("GET", "/storage/download", response.status, duration, result.message);
      return result;
    },

    async animateFlow(flow) {
      this.resetTopology();
      this.flowSteps = (flow || []).map((step) => ({
        node: step.node,
        status: step.status,
        detail: step.detail,
      }));
      for (let i = 0; i < this.flowSteps.length; i++) {
        const step = this.flowSteps[i];
        this.flowStepIndex = i;
        if (this.activeNodes[step.node]) {
          this.activeNodes[step.node] = {
            active: true,
            status: step.status,
            detail: step.detail,
          };
        }
        // Pausa maior a cada passo para o aluno acompanhar o roteiro
        await new Promise((resolve) => setTimeout(resolve, 420));
      }
    },

    flowStepClass(index) {
      if (index > this.flowStepIndex) return "border-slate-800 bg-slate-950/40 opacity-50";
      const step = this.flowSteps[index];
      const ok = step && step.status >= 400 ? false : true;
      if (index === this.flowStepIndex) {
        return ok
          ? "border-cyan-400 bg-cyan-500/15 shadow-lg shadow-cyan-500/10"
          : "border-rose-400 bg-rose-500/15 shadow-lg shadow-rose-500/10";
      }
      return ok
        ? "border-emerald-400/50 bg-emerald-500/5"
        : "border-rose-400/50 bg-rose-500/5";
    },

    statusColorClass(status) {
      if (status >= 400) return "bg-rose-500/20 text-rose-100";
      if (status >= 200 && status < 300) return "bg-emerald-500/20 text-emerald-100";
      return "bg-slate-800 text-slate-300";
    },

    addLog(method, endpoint, status, duration, message) {
      this.logs.unshift({
        id: `${Date.now()}-${Math.random()}`,
        method,
        endpoint,
        status,
        duration,
        message,
        timestamp: new Date().toLocaleTimeString("pt-BR"),
      });
    },

    pretty(value) {
      return value ? JSON.stringify(value, null, 2) : "";
    },
  }));
});

document.addEventListener("alpine:init", () => {
  Alpine.data("adminPanel", () => ({
    activeTab: "users",
    users: [],
    grades: [],
    courseLocks: [],
    newUser: {
      username: "",
      subject: "",
      name: "",
      label: "",
      roles: "aluno",
      scopes: "notas:read storage:download",
      department: "",
      academic_unit: "sistemas",
      clearance: 1,
      can_grade: false,
      storage_tier: "basic",
      active: true,
    },
    message: "",
    error: "",

    async init() {
      await this.loadAll();
    },

    async loadAll() {
      await Promise.all([this.loadUsers(), this.loadGrades(), this.loadCourseLocks()]);
    },

    async loadUsers() {
      try {
        const r = await fetch("/admin/users");
        this.users = await r.json();
      } catch (e) {
        this.error = e.message;
      }
    },

    async loadGrades() {
      try {
        const r = await fetch("/admin/grades");
        this.grades = await r.json();
      } catch (e) {
        this.error = e.message;
      }
    },

    async loadCourseLocks() {
      try {
        const r = await fetch("/admin/course-locks");
        this.courseLocks = await r.json();
      } catch (e) {
        this.error = e.message;
      }
    },

    async createUser() {
      const body = {
        ...this.newUser,
        roles: this.newUser.roles.split(/\s+/).filter(Boolean),
        scopes: this.newUser.scopes.split(/\s+/).filter(Boolean),
        clearance: Number(this.newUser.clearance),
      };
      if (!body.subject) body.subject = body.username;
      if (!body.label) body.label = body.name;
      const r = await fetch("/admin/users", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (r.ok) {
        this.message = "Usuário criado com sucesso.";
        this.newUser = { username: "", subject: "", name: "", label: "", roles: "aluno", scopes: "notas:read storage:download", department: "", academic_unit: "sistemas", clearance: 1, can_grade: false, storage_tier: "basic", active: true };
        await this.loadUsers();
      } else {
        const err = await r.json();
        this.error = err.detail || "Erro ao criar usuário.";
      }
    },

    async toggleActive(user) {
      const r = await fetch(`/admin/users/${user.username}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ active: !user.active }),
      });
      if (r.ok) {
        await this.loadUsers();
      } else {
        this.error = "Erro ao atualizar usuário.";
      }
    },

    async deleteUser(username) {
      if (!confirm(`Remover usuário "${username}"?`)) return;
      const r = await fetch(`/admin/users/${username}`, { method: "DELETE" });
      if (r.ok || r.status === 204) {
        await this.loadUsers();
      } else {
        this.error = "Erro ao remover usuário.";
      }
    },

    async deleteGrade(id) {
      if (!confirm(`Remover nota #${id}?`)) return;
      const r = await fetch(`/admin/grades/${id}`, { method: "DELETE" });
      if (r.ok || r.status === 204) {
        await this.loadGrades();
      } else {
        this.error = "Erro ao remover nota.";
      }
    },

    async deleteCourseLock(id) {
      if (!confirm(`Remover trancamento #${id}?`)) return;
      const r = await fetch(`/admin/course-locks/${id}`, { method: "DELETE" });
      if (r.ok || r.status === 204) {
        await this.loadCourseLocks();
      } else {
        this.error = "Erro ao remover trancamento.";
      }
    },
  }));
});
