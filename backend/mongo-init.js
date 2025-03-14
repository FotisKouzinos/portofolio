const { execSync } = require("child_process");

conn = new Mongo("mongodb://admin:pass@mongodb:27017/");
db = conn.getDB("ApiB");

if (db.system.users.find({ user: "admin" }).count() === 0) {
  db.createUser({
    user: "admin",
    pwd: "pass",
    roles: [{ role: "readWrite", db: "ApiB" }]
  });
}


db.students.drop();
db.hub.drop();

function runShellCommand(command) {
  try {
    execSync(command, { stdio: "inherit" });
  } catch (error) {
    print("Error running command: " + command);
  }
}


runShellCommand('mongoimport --host mongodb --port 27017 --username admin --password pass --authenticationDatabase admin --db ApiB --collection students --file /apib/ApiB/backend/students.json');

runShellCommand('mongoimport --host mongodb --port 27017 --username admin --password pass --authenticationDatabase admin --db ApiB --collection hub --file /apib/ApiB/backend/hubs.json');

print("MongoDB initialization complete.");