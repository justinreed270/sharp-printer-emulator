import React, { useState } from 'react';

export default function App() {
  const [authenticated, setAuthenticated] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [testResults, setTestResults] = useState([]);
  const [testStatus, setTestStatus] = useState('');

  const [smtpConfig, setSmtpConfig] = useState({
    primaryGateway: '',
    primaryPort: '587',
    replyAddress: '',
    useSSL: 'negotiate',
    smtpAuth: 'login-plain',
    deviceUserid: '',
    devicePassword: ''
  });

  const handleLogin = () => {
    if (username === import.meta.env.VITE_APP_USERNAME && password === import.meta.env.VITE_APP_PASSWORD) {
      setAuthenticated(true);
    } else {
      alert('Hmmm - Try again. You have invalid credentials. ');
    }
  };

  const handleSave = () => {
    console.log('=== SMTP Configuration Saved ===');
    console.log('Primary SMTP Gateway:', smtpConfig.primaryGateway);
    console.log('Port:', smtpConfig.primaryPort);
    console.log('Reply Address:', smtpConfig.replyAddress);
    console.log('SSL/TLS:', smtpConfig.useSSL);
    console.log('Authentication:', smtpConfig.smtpAuth);
    console.log('Device Userid:', smtpConfig.deviceUserid);
    console.log('================================');
    alert('Configuration saved! Check console.');
  };

  const handleTestConnection = async () => {
    setTestStatus('testing');
    setTestResults([]);
    
    try {
      // Call the Python backend API
      const response = await fetch('http://localhost:8000/test-smtp', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          primaryGateway: smtpConfig.primaryGateway,
          primaryPort: parseInt(smtpConfig.primaryPort),
          replyAddress: smtpConfig.replyAddress,
          useSSL: smtpConfig.useSSL,
          smtpAuth: smtpConfig.smtpAuth,
          deviceUserid: smtpConfig.deviceUserid,
          devicePassword: smtpConfig.devicePassword
        })
      });

      const data = await response.json();
      
      setTestResults(data.details);
      setTestStatus(data.success ? 'success' : 'failed');

    } catch (error) {
      setTestResults([{
        type: 'error',
        message: `✗ Failed to connect to validation service: ${error.message}`
      }]);
      setTestStatus('failed');
    }

    setTimeout(() => setTestStatus(''), 5000);
  };

  const updateConfig = (field, value) => {
    setSmtpConfig(prev => ({ ...prev, [field]: value }));
  };

  if (!authenticated) {
    return (
      <div style={{ maxWidth: '400px', margin: '100px auto', padding: '20px', border: '1px solid #ccc', borderRadius: '8px', backgroundColor: 'white' }}>
        <h1>SHARP MX-B468F</h1>
        <p>Web Management</p>
        <div style={{ marginTop: '20px' }}>
          <label>Username:</label>
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleLogin()}
            style={{ width: '100%', padding: '8px', marginTop: '5px' }}
          />
        </div>
        <div style={{ marginTop: '15px' }}>
          <label>Password:</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleLogin()}
            style={{ width: '100%', padding: '8px', marginTop: '5px' }}
          />
        </div>
        <button onClick={handleLogin} style={{ marginTop: '20px', width: '100%', padding: '10px', background: '#0066cc', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
          Login
        </button>
        
      </div>
    );
  }

  return (
    <div style={{ padding: '20px', maxWidth: '900px', margin: '0 auto', backgroundColor: '#f5f5f5', minHeight: '100vh' }}>
      <div style={{ background: '#0066cc', color: 'white', padding: '15px', marginBottom: '20px', borderRadius: '8px' }}>
        <h1 style={{ margin: 0 }}>SHARP MX-B468F - Email Setup</h1>
        <p style={{ margin: '5px 0 0 0', fontSize: '14px' }}>Scan to Email Configuration</p>
      </div>

      <div style={{ backgroundColor: 'white', border: '1px solid #ddd', padding: '25px', borderRadius: '8px', marginBottom: '20px' }}>
        <h2 style={{ marginTop: 0, borderBottom: '2px solid #0066cc', paddingBottom: '10px' }}>SMTP Gateway Configuration</h2>
        
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px', marginTop: '20px' }}>
          <div>
            <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '5px' }}>Primary SMTP Gateway *</label>
            <input
              type="text"
              value={smtpConfig.primaryGateway}
              onChange={(e) => updateConfig('primaryGateway', e.target.value)}
              placeholder="smtp.gmail.com"
              style={{ width: '100%', padding: '8px', border: '1px solid #ccc', borderRadius: '4px' }}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '5px' }}>Port *</label>
            <input
              type="text"
              value={smtpConfig.primaryPort}
              onChange={(e) => updateConfig('primaryPort', e.target.value)}
              style={{ width: '100%', padding: '8px', border: '1px solid #ccc', borderRadius: '4px' }}
            />
          </div>

          <div style={{ gridColumn: '1 / -1' }}>
            <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '5px' }}>Reply Address *</label>
            <input
              type="email"
              value={smtpConfig.replyAddress}
              onChange={(e) => updateConfig('replyAddress', e.target.value)}
              placeholder="printer@example.com"
              style={{ width: '100%', padding: '8px', border: '1px solid #ccc', borderRadius: '4px' }}
            />
          </div>
        </div>

        <h3 style={{ marginTop: '30px', borderBottom: '2px solid #0066cc', paddingBottom: '10px' }}>Security & Authentication</h3>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px', marginTop: '20px' }}>
          <div>
            <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '5px' }}>USE SSL/TLS</label>
            <select
              value={smtpConfig.useSSL}
              onChange={(e) => updateConfig('useSSL', e.target.value)}
              style={{ width: '100%', padding: '8px', border: '1px solid #ccc', borderRadius: '4px' }}
            >
              <option value="none">None</option>
              <option value="negotiate">Negotiate</option>
              <option value="ssl">SSL</option>
              <option value="tls">TLS</option>
            </select>
          </div>

          <div>
            <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '5px' }}>Authentication</label>
            <select
              value={smtpConfig.smtpAuth}
              onChange={(e) => updateConfig('smtpAuth', e.target.value)}
              style={{ width: '100%', padding: '8px', border: '1px solid #ccc', borderRadius: '4px' }}
            >
              <option value="none">None</option>
              <option value="login-plain">Login/Plain</option>
              <option value="cram-md5">CRAM-MD5</option>
            </select>
          </div>
        </div>

        <h3 style={{ marginTop: '30px', borderBottom: '2px solid #0066cc', paddingBottom: '10px' }}>Device SMTP Credentials</h3>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px', marginTop: '20px' }}>
          <div>
            <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '5px' }}>Device Userid</label>
            <input
              type="text"
              value={smtpConfig.deviceUserid}
              onChange={(e) => updateConfig('deviceUserid', e.target.value)}
              placeholder="printer@example.com"
              style={{ width: '100%', padding: '8px', border: '1px solid #ccc', borderRadius: '4px' }}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '5px' }}>Device Password</label>
            <input
              type="password"
              value={smtpConfig.devicePassword}
              onChange={(e) => updateConfig('devicePassword', e.target.value)}
              style={{ width: '100%', padding: '8px', border: '1px solid #ccc', borderRadius: '4px' }}
            />
          </div>
        </div>

        <div style={{ marginTop: '30px', display: 'flex', gap: '15px' }}>
          <button 
            onClick={handleSave} 
            style={{ padding: '12px 30px', background: '#0066cc', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold', fontSize: '14px' }}
          >
            Submit
          </button>

          <button 
            onClick={handleTestConnection}
            disabled={testStatus === 'testing'}
            style={{ 
              padding: '12px 30px', 
              background: testStatus === 'testing' ? '#999' : '#28a745', 
              color: 'white', 
              border: 'none', 
              borderRadius: '4px', 
              cursor: testStatus === 'testing' ? 'not-allowed' : 'pointer', 
              fontWeight: 'bold',
              fontSize: '14px'
            }}
          >
            {testStatus === 'testing' ? '🔄 Testing...' : '🔌 Test REAL Connection'}
          </button>
        </div>
      </div>

      {/* Test Results Panel */}
      {testResults.length > 0 && (
        <div style={{ 
          backgroundColor: '#1a1a1a', 
          color: '#e0e0e0', 
          padding: '20px', 
          borderRadius: '8px', 
          fontFamily: 'monospace',
          fontSize: '13px',
          marginBottom: '20px',
          boxShadow: '0 4px 6px rgba(0,0,0,0.3)'
        }}>
          <h3 style={{ margin: '0 0 15px 0', color: '#4CAF50' }}>📋 REAL SMTP Test Results:</h3>
          <div style={{ lineHeight: '1.8' }}>
            {testResults.map((result, idx) => (
              <div
                key={idx}
                style={{
                  color: 
                    result.type === 'error' ? '#ff6b6b' :
                    result.type === 'warning' ? '#ffa500' :
                    result.type === 'success' ? '#4CAF50' :
                    '#b0b0b0',
                  marginBottom: '5px'
                }}
              >
                {result.message}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Success/Failure Banner */}
      {testStatus === 'success' && (
        <div style={{ 
          backgroundColor: '#d4edda', 
          color: '#155724', 
          padding: '15px', 
          borderRadius: '8px',
          border: '2px solid #c3e6cb',
          marginBottom: '20px',
          fontWeight: 'bold'
        }}>
          ✅ REAL SMTP CONNECTION SUCCESSFUL! Your credentials are valid and the server is accepting connections.
        </div>
      )}

      {testStatus === 'failed' && (
        <div style={{ 
          backgroundColor: '#f8d7da', 
          color: '#721c24', 
          padding: '15px', 
          borderRadius: '8px',
          border: '2px solid #f5c6cb',
          marginBottom: '20px',
          fontWeight: 'bold'
        }}>
          ❌ SMTP CONNECTION FAILED. Check the errors above - this was a real connection test!
        </div>
      )}

      <div style={{ 
        backgroundColor: '#fff3cd', 
        border: '1px solid #ffc107', 
        padding: '15px', 
        borderRadius: '8px',
        marginTop: '20px'
      }}>
        <p style={{ margin: 0, fontSize: '13px' }}>
          <strong>🔒 Security Note:</strong> This performs REAL SMTP authentication tests. 
          Never use production credentials in testing environments. Use test accounts only.
        </p>
      </div>
    </div>
  );
}