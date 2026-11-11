import React, { useEffect, useState } from 'react';
import { Bell, CheckCircle, RefreshCw, Send, XCircle } from 'lucide-react';
import { api } from '../services/api';
import { NotificationRecord, TelegramStatus } from '../types';

export const NotificationsPage: React.FC = () => {
  const [status, setStatus] = useState<TelegramStatus | null>(null);
  const [notifications, setNotifications] = useState<NotificationRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [testing, setTesting] = useState(false);
  const [retryingId, setRetryingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);

  const refresh = async () => {
    setLoading(true);
    setError(null);
    try {
      const [telegramStatus, history] = await Promise.all([
        api.getTelegramStatus(),
        api.getNotifications()
      ]);
      setStatus(telegramStatus);
      setNotifications(history.items);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : String(requestError));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void refresh();
  }, []);

  const testConnection = async () => {
    setTesting(true);
    setFeedback(null);
    try {
      const result = await api.testTelegramConnection();
      setFeedback(result.status === 'DELIVERED'
        ? 'Telegram accepted the test notification.'
        : `Telegram delivery failed: ${result.error_code || 'Unknown delivery error'}`);
      await refresh();
    } catch (requestError) {
      setFeedback(requestError instanceof Error ? requestError.message : String(requestError));
      await refresh();
    } finally {
      setTesting(false);
    }
  };

  const retry = async (notificationId: string) => {
    setRetryingId(notificationId);
    setFeedback(null);
    try {
      const result = await api.retryNotification(notificationId);
      setFeedback(result.status === 'DELIVERED'
        ? 'Telegram accepted the retry.'
        : `Retry failed: ${result.error_code || 'Unknown delivery error'}`);
      await refresh();
    } catch (requestError) {
      setFeedback(requestError instanceof Error ? requestError.message : String(requestError));
      await refresh();
    } finally {
      setRetryingId(null);
    }
  };

  const configurationLabel = !status?.enabled
    ? 'Disabled'
    : !status.configured
      ? 'Credentials missing'
      : status.connection_status === 'connected'
        ? 'Connected'
        : status.connection_status === 'error'
          ? 'Last test failed'
          : 'Configured — test required';
  const chatNotFound = notifications.some(
    (notification) =>
      !notification.alert_id
      && notification.status === 'FAILED'
      && notification.error_code?.toLowerCase().includes('chat not found')
  );

  return (
    <div className="page-container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 16, marginBottom: 24 }}>
        <div>
          <h1 style={{ color: 'var(--text-main)', marginBottom: 6 }}>Telegram Notifications</h1>
          <p style={{ color: 'var(--text-muted)' }}>Delivery records for incident alerts and connection tests.</p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn btn-secondary" onClick={() => void refresh()} disabled={loading}>
            <RefreshCw size={15} className={loading ? 'animate-spin' : ''} />
            Refresh
          </button>
          <button className="btn btn-primary" onClick={() => void testConnection()} disabled={testing || !status?.enabled || !status.configured}>
            <Send size={15} />
            {testing ? 'Sending test…' : 'Test Telegram'}
          </button>
        </div>
      </div>

      {feedback && (
        <div className="glass-card" role="status" style={{ padding: 14, marginBottom: 16, color: 'var(--text-main)' }}>
          {feedback}
        </div>
      )}
      {error && (
        <div className="glass-card" role="alert" style={{ padding: 14, marginBottom: 16, color: '#f87171' }}>
          Could not load notification data: {error}
        </div>
      )}

      <div className="glass-card" style={{ padding: 20, marginBottom: 20 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
          <Bell size={20} color="var(--color-accent)" />
          <div>
            <h2 style={{ color: 'var(--text-main)', fontSize: '1.05rem' }}>Telegram connection</h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              {status?.recipient_hint ? `Recipient: ${status.recipient_hint}` : 'Recipient details are not configured.'}
            </p>
          </div>
          <strong style={{ marginLeft: 'auto', color: status?.connection_status === 'connected' ? 'var(--color-normal)' : 'var(--color-warning)' }}>
            {status ? configurationLabel : 'Checking…'}
          </strong>
        </div>
        <div className="grid-4">
          <div><strong>{status?.total_messages ?? 0}</strong><p style={{ color: 'var(--text-muted)' }}>Total attempts</p></div>
          <div><strong>{status?.delivered_messages ?? 0}</strong><p style={{ color: 'var(--text-muted)' }}>Delivered</p></div>
          <div><strong>{status?.failed_messages ?? 0}</strong><p style={{ color: 'var(--text-muted)' }}>Failed</p></div>
          <div>
            <strong>{status?.last_notification_time ? new Date(status.last_notification_time).toLocaleString() : '—'}</strong>
            <p style={{ color: 'var(--text-muted)' }}>Last attempt</p>
          </div>
        </div>
        {!status?.enabled && (
          <p style={{ marginTop: 16, color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            Set <code>TELEGRAM_ENABLED=true</code> and configure the bot token and chat ID in the backend environment. Secrets are not shown in this page.
          </p>
        )}
        {chatNotFound && (
          <p role="alert" style={{ marginTop: 16, color: 'var(--color-warning)', fontSize: '0.85rem' }}>
            Telegram could not find this chat. Open @fire_alret_agent_bot, send /start, verify the chat ID in the backend .env, restart the backend, then send another test. Never paste the bot token into chat.
          </p>
        )}
      </div>

      <div className="glass-card" style={{ padding: 20 }}>
        <h2 style={{ color: 'var(--text-main)', fontSize: '1.05rem', marginBottom: 16 }}>Notification history</h2>
        {loading && notifications.length === 0 ? (
          <p style={{ color: 'var(--text-muted)' }}>Loading notification history…</p>
        ) : notifications.length === 0 ? (
          <div style={{ padding: 32, textAlign: 'center', color: 'var(--text-muted)' }}>
            <CheckCircle size={28} style={{ marginBottom: 8 }} />
            <p>No Telegram notification attempts have been recorded.</p>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Recipient</th>
                  <th>Incident</th>
                  <th>Message</th>
                  <th>Status</th>
                  <th>Retries</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {notifications.map((notification) => (
                  <tr key={notification.id}>
                    <td>{new Date(notification.attempted_at).toLocaleString()}</td>
                    <td>{notification.recipient ? `****${notification.recipient.slice(-4)}` : '—'}</td>
                    <td>{notification.alert_id || 'Connection test'}</td>
                    <td style={{ minWidth: 240, maxWidth: 420, whiteSpace: 'pre-wrap' }}>
                      {notification.message || '—'}
                      {notification.error_code && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: 5, marginTop: 6, color: '#f87171', fontSize: '0.78rem' }}>
                          <XCircle size={13} /> {notification.error_code}
                        </div>
                      )}
                    </td>
                    <td>
                      <span className={`badge ${notification.status === 'DELIVERED' ? 'badge-normal' : 'badge-fire'}`}>
                        {notification.status}
                      </span>
                    </td>
                    <td>{notification.retry_count}</td>
                    <td>
                      {notification.status === 'FAILED' && (
                        <button
                          className="btn btn-secondary"
                          onClick={() => void retry(notification.id)}
                          disabled={retryingId !== null}
                        >
                          <RefreshCw size={14} className={retryingId === notification.id ? 'animate-spin' : ''} />
                          Retry
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
