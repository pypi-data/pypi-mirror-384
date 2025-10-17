import * as React from 'react';
import { Form } from 'react-bootstrap';

/**
 * Snowflake-specific form data interface
 */
export interface SnowflakeFormData {
  connectionUrl: string;
  username: string;
  password: string;
  database?: string;
  warehouse?: string;
  role?: string;
}

/**
 * Props for the SnowflakeDataForm component
 */
export interface SnowflakeDataFormProps {
  formData: SnowflakeFormData;
  errors: Partial<SnowflakeFormData>;
  isSubmitting: boolean;
  onFieldChange: (field: keyof SnowflakeFormData, value: string) => void;
}

/**
 * Snowflake database connection form component
 */
export function SnowflakeDataForm({
  formData,
  errors,
  isSubmitting,
  onFieldChange
}: SnowflakeDataFormProps): JSX.Element {
  return (
    <>
      {/* Documentation Link */}
      <div className="form-section-compact">
        <div className="form-row-compact form-row-compact-reduced">
          <div className="form-input-wrapper" style={{ width: '100%' }}>
            <a
              href="https://docs.signalpilot.ai/guide/core/connecting-databases/connecting-a-snowflake-database"
              target="_blank"
              rel="noopener noreferrer"
              className="documentation-link"
              style={{
                textDecoration: 'none',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px',
                fontSize: '0.875rem'
              }}
            >
              View Snowflake connection instructions
              <span style={{ fontSize: '0.75rem' }}>↗</span>
            </a>
          </div>
        </div>
      </div>

      <div className="form-section-compact">
        {/* Connection URL */}
        <div className="form-row-compact form-row-compact-reduced">
          <label htmlFor="connectionUrl" className="form-label-inline">
            Connection URL <span className="text-danger">*</span>
          </label>
          <div className="form-input-wrapper">
            <Form.Control
              id="connectionUrl"
              type="text"
              value={formData.connectionUrl}
              onChange={e => onFieldChange('connectionUrl', e.target.value)}
              isInvalid={!!errors.connectionUrl}
              placeholder="https://account-region.snowflakecomputing.com"
              disabled={isSubmitting}
              className="form-control-compact"
              autoComplete="off"
              data-form-type="other"
              spellCheck={false}
            />
            {errors.connectionUrl && (
              <div className="invalid-feedback-inline">
                {errors.connectionUrl}
              </div>
            )}
          </div>
        </div>

        {/* Username */}
        <div className="form-row-compact form-row-compact-reduced">
          <label htmlFor="username" className="form-label-inline">
            Username <span className="text-danger">*</span>
          </label>
          <div className="form-input-wrapper">
            <Form.Control
              id="username"
              type="text"
              value={formData.username}
              onChange={e => onFieldChange('username', e.target.value)}
              isInvalid={!!errors.username}
              placeholder="Snowflake username"
              disabled={isSubmitting}
              className="form-control-compact"
              autoComplete="off"
              data-form-type="other"
              spellCheck={false}
            />
            {errors.username && (
              <div className="invalid-feedback-inline">{errors.username}</div>
            )}
          </div>
        </div>

        {/* Password */}
        <div className="form-row-compact form-row-compact-reduced">
          <label htmlFor="password" className="form-label-inline">
            Password <span className="text-danger">*</span>
          </label>
          <div className="form-input-wrapper">
            <Form.Control
              id="password"
              type="password"
              value={formData.password}
              onChange={e => onFieldChange('password', e.target.value)}
              isInvalid={!!errors.password}
              placeholder="Snowflake password"
              disabled={isSubmitting}
              className="form-control-compact"
              autoComplete="new-password"
              data-form-type="other"
            />
            {errors.password && (
              <div className="invalid-feedback-inline">{errors.password}</div>
            )}
          </div>
        </div>

        {/* Database (Optional) */}
        <div className="form-row-compact form-row-compact-reduced">
          <label htmlFor="database" className="form-label-inline">
            Database
          </label>
          <div className="form-input-wrapper">
            <Form.Control
              id="database"
              type="text"
              value={formData.database || ''}
              onChange={e => onFieldChange('database', e.target.value)}
              placeholder="Optional database name"
              disabled={isSubmitting}
              className="form-control-compact"
              autoComplete="off"
              data-form-type="other"
              spellCheck={false}
            />
          </div>
        </div>

        {/* Warehouse (Optional) */}
        <div className="form-row-compact form-row-compact-reduced">
          <label htmlFor="warehouse" className="form-label-inline">
            Warehouse
          </label>
          <div className="form-input-wrapper">
            <Form.Control
              id="warehouse"
              type="text"
              value={formData.warehouse || ''}
              onChange={e => onFieldChange('warehouse', e.target.value)}
              placeholder="Optional warehouse name"
              disabled={isSubmitting}
              className="form-control-compact"
              autoComplete="off"
              data-form-type="other"
              spellCheck={false}
            />
          </div>
        </div>

        {/* Role (Optional) */}
        <div className="form-row-compact form-row-compact-reduced">
          <label htmlFor="role" className="form-label-inline">
            Role
          </label>
          <div className="form-input-wrapper">
            <Form.Control
              id="role"
              type="text"
              value={formData.role || ''}
              onChange={e => onFieldChange('role', e.target.value)}
              placeholder="Optional role name"
              disabled={isSubmitting}
              className="form-control-compact"
              autoComplete="off"
              data-form-type="other"
              spellCheck={false}
            />
          </div>
        </div>

        {/* Security Notice */}
        <div className="security-notice-compact mt-3">
          <span className="notice-icon-small">🛡️</span>
          <span className="notice-text-compact">
            All credentials are encrypted using AES-256 encryption and never
            leave your local machine
          </span>
        </div>
      </div>
    </>
  );
}
