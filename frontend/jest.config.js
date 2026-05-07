const { createDefaultPreset } = require('ts-jest');

const tsJestTransformCfg = createDefaultPreset().transform;

/** @type {import("jest").Config} **/
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1',
    '^@layouts/(.*)$': '<rootDir>/components/layout/$1',
    '^@auth/(.*)$': '<rootDir>/hooks/auth/$1',
    '^@authlanding/(.*)$': '<rootDir>/components/auth/AuthLanding/$1',
    '^@contributions/(.*)$': '<rootDir>/components/contributions/$1',
    '^@project/(.*)$': '<rootDir>/components/project/$1',
    '^@shared/(.*)$': '<rootDir>/components/shared/$1',
    '^@users/(.*)$': '<rootDir>/components/users/$1',
  },
};
