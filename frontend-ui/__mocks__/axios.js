module.exports = {
  post: jest.fn(),
  put: jest.fn(),
  get: jest.fn(),
  create: jest.fn(() => ({
    post: jest.fn(),
    put: jest.fn(),
    get: jest.fn()
  }))
};
