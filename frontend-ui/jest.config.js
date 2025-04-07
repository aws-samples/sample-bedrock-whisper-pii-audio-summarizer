module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/src/setupTests.js'],
  moduleNameMapper: {
    '\\.(css|less|sass|scss)$': '<rootDir>/__mocks__/styleMock.js',
    '\\.(gif|ttf|eot|svg)$': '<rootDir>/__mocks__/fileMock.js'
  },
  transformIgnorePatterns: [
    "node_modules/(?!(axios|@bundled-es-modules)/)"
  ],
  moduleNameMapper: {
    "^axios$": "<rootDir>/node_modules/axios/dist/axios.js"
  },
  transform: {
    '^.+\\.(js|jsx|ts|tsx)$': 'babel-jest'
  }
};
