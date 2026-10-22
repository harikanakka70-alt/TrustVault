
import { useState } from 'react'
import { login } from './api'
import './App.css'

const roles = [
    { id: 'admin', title: 'Administrator', icon: '🛡️', description: 'Manage users, documents, and audit activity.' },
    { id: 'owner', title: 'Document Owner', icon: '📁', description: 'Upload documents and manage access to your files.' },
    { id: 'viewer', title: 'Viewer', icon: '👁️', description: 'Access documents your account is permitted to view.' },
]

function App() {
    const [selectedRole, setSelectedRole] = useState(null)
    const [username, setUsername] = useState('')
    const [password, setPassword] = useState('')
    const [session, setSession] = useState(null)
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)

    async function handleLogin(event) {
        event.preventDefault()
        setError('')
        setLoading(true)

        try {
            const result = await login(username.trim(), password)
            const token = result.access_token
            const payload = JSON.parse(atob(token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')))
            const actualRole = payload.role

            if (!['admin', 'owner', 'viewer'].includes(actualRole)) {
                throw new Error('Your account has an unrecognized role.')
            }

            if (actualRole !== selectedRole.id) {
                throw new Error(`This account is a ${actualRole} account. Select the matching workspace.`)
            }

            setSession({ token, username: payload.sub || username, role: actualRole })
            setPassword('')
        } catch (err) {
            setError(err.message || 'Login failed. Check your credentials and try again.')
        } finally {
            setLoading(false)
        }
    }

    function backToRoles() {
        setSelectedRole(null)
        setSession(null)
        setUsername('')
        setPassword('')
        setError('')
    }

    return (
        <main className="app">
            <header className="topbar">
                <a className="brand" href="#" onClick={(event) => { event.preventDefault(); backToRoles() }}>
                    <span className="brand-icon">T</span>
                    <span>TrustVault</span>
                </a>
                <span className="security-label"><span className="status-dot" /> Secure Document Management</span>
            </header>

            {!selectedRole ? (
                <section className="role-screen">
                    <div className="eyebrow">YOUR DOCUMENTS. YOUR CONTROL.</div>
                    <h1>Welcome to TrustVault</h1>
                    <p className="subtitle">Choose your workspace, then sign in with your existing TrustVault account.</p>
                    <div className="role-list">
                        {roles.map((role) => (
                            <button key={role.id} className="role-card" onClick={() => { setSelectedRole(role); setError('') }}>
                                <span className="role-icon">{role.icon}</span>
                                <span className="role-copy"><strong>{role.title}</strong><span>{role.description}</span></span>
                                <span className="role-arrow" aria-hidden="true">→</span>
                            </button>
                        ))}
                    </div>
                    <p className="footnote">Workspace selection does not grant permissions. Your account role is checked after login.</p>
                </section>
            ) : !session ? (
                <section className="dashboard">
                    <button className="back-button" onClick={backToRoles}>← Back to roles</button>
                    <div className="dashboard-icon">{selectedRole.icon}</div>
                    <div className="eyebrow">TRUSTVAULT SECURE SIGN-IN</div>
                    <h1>{selectedRole.title}</h1>
                    <p className="subtitle">Sign in using an account already registered with TrustVault.</p>

                    <form className="login-form" onSubmit={handleLogin}>
                        <label htmlFor="username">Username</label>
                        <input id="username" autoComplete="username" value={username} onChange={(e) => setUsername(e.target.value)} required />
                        <label htmlFor="password">Password</label>
                        <input id="password" type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} required />
                        {error && <p className="error-message" role="alert">{error}</p>}
                        <button className="primary-button" type="submit" disabled={loading}>
                            {loading ? 'Signing in…' : 'Sign in securely'}
                        </button>
                    </form>
                </section>
            ) : (
                <section className="dashboard">
                    <button className="back-button" onClick={backToRoles}>← Sign out</button>
                    <div className="dashboard-icon">{selectedRole.icon}</div>
                    <div className="eyebrow">AUTHENTICATED WORKSPACE</div>
                    <h1>Welcome, {session.username}</h1>
                    <p className="subtitle">Your server-verified role is <strong>{session.role}</strong>.</p>
                    <div className="notice">
                        <strong>Authentication successful</strong>
                        <p>You are signed in. Next we'll connect the document, permission, user-management, and audit features to the existing API.</p>
                    </div>
                    <p className="footnote">Keep your access token private. The backend must authorize each protected request.</p>
                </section>
            )}

            <footer><span>TrustVault</span><span>Confidential documents, protected access.</span></footer>
        </main>
    )
}

export default App
