import React from 'react';

export interface NotificationBadgeProps {
  type: 'success' | 'error';
  message: string;
  show: boolean;
  style?: React.CSSProperties;
}

const NotificationBadge: React.FC<NotificationBadgeProps> = ({
  type,
  message,
  show,
  style,
}) => (
  <div
    role="alert"
    aria-live="assertive"
    className={`fixed z-50 px-6 py-3 rounded shadow-lg text-center font-semibold text-base transition-opacity duration-500
      ${type === 'success' ? 'bg-green-100 text-green-800 border border-green-300' : 'bg-red-100 text-red-800 border border-red-300'}
      ${show ? 'opacity-100' : 'opacity-0'}`}
    style={style}
  >
    {message}
  </div>
);

export default NotificationBadge;
