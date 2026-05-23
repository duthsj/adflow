module.exports = {
  apps: [
    {
      name: "muelaads-backend",
      cwd: ".",
      script: "uvicorn",
      args: "backend.main:app --host 0.0.0.0 --port 8000",
      interpreter: "none",
    },
    {
      name: "muelaads-frontend",
      cwd: "./frontend",
      script: "npm",
      args: "run dev",
      interpreter: "none",
      env: {
        PORT: "3000",
        NEXT_PUBLIC_API_URL: "http://localhost:8000",
      },
    },
  ],
};
