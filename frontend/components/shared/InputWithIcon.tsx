import React from 'react';

export interface InputWithIconProps {
  type: string;
  name?: string;
  value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  icon: React.ReactNode;
  ariaLabel?: string;
  placeholder?: string;
  autoComplete?: string;
}

const InputWithIcon: React.FC<InputWithIconProps> = ({
  type,
  name,
  value,
  onChange,
  icon,
  ariaLabel,
  placeholder,
  autoComplete,
}) => (
  <div className="relative">
    <span className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
      {icon}
    </span>
    <input
      type={type}
      name={name}
      className="pl-10 p-2 border rounded w-full"
      aria-label={ariaLabel}
      placeholder={placeholder}
      value={value}
      onChange={onChange}
      autoComplete={autoComplete}
    />
  </div>
);

export default InputWithIcon;
