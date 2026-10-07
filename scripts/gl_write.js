// Send a Studionet write transaction with exact, explicit argument types,
// bypassing two real bugs found in `genlayer write`'s --args heuristic
// (genlayer CLI 0.39.2, see docs/DEPLOYMENT.md):
//
//   1. Any argument whose text is valid JSON for an object/array (e.g. a
//      JSON-encoded policy string meant to be passed through AS A STRING)
//      gets silently coerced into a dict/array argument instead of the
//      plain string the contract's ABI expects. seal_asset_definition's
//      policy_json parameter hit this directly.
//   2. An empty string argument ("") is coerced to the number 0
//      (`Number("") === 0` in JS), breaking any str-typed parameter that
//      is legitimately empty, e.g. add_component's root-category parent_id.
//
// Both failures manifest as a GenVM `contract_error: exit_code 1` with no
// state change -- a safe failure, but one that looks identical to a real
// contract bug unless you inspect the full receipt's calldata.
//
// This script reuses the exact same signer resolution path the CLI itself
// uses (keytar service "genlayer-cli", account "account:<name>"), so the
// private key is read once into memory and handed straight to
// createAccount -- it is never printed or logged here.
//
// Usage: node scripts/gl_write.js <accountName> <contractAddress> <method> <argsJsonArray>
// argsJsonArray is a JSON array of the exact argument values, e.g.
//   '["A2", "{\"a\":1}"]'
const path = require("path");
const { execSync } = require("child_process");

function resolveGenlayerCliDir() {
  if (process.env.GENLAYER_CLI_DIR) return process.env.GENLAYER_CLI_DIR;
  const npmRoot = execSync("npm root -g").toString().trim();
  return path.join(npmRoot, "genlayer");
}

const genlayerCliDir = resolveGenlayerCliDir();
const gl = require(path.join(genlayerCliDir, "node_modules/genlayer-js"));
const keytar = require(path.join(genlayerCliDir, "node_modules/keytar"));

async function main() {
  const [accountName, contractAddress, method, argsJson] = process.argv.slice(2);
  const args = JSON.parse(argsJson);

  const privateKey = await keytar.getPassword("genlayer-cli", `account:${accountName}`);
  if (!privateKey) {
    console.error(`No cached private key for account '${accountName}' (is it unlocked?)`);
    process.exit(2);
  }
  const account = gl.createAccount(privateKey);
  const client = gl.createClient({ chain: gl.chains.studionet, account });
  await client.initializeConsensusSmartContract();

  const hash = await client.writeContract({
    address: contractAddress,
    functionName: method,
    args,
    value: 0n,
  });
  console.log("Write Transaction Hash:", hash);

  const receipt = await client.waitForTransactionReceipt({ hash, retries: 100, interval: 5000 });
  console.log(JSON.stringify(receipt, (_k, v) => (typeof v === "bigint" ? v.toString() : v), 2));
}

main().catch((err) => {
  console.error("ERROR:", err && err.message ? err.message : err);
  process.exit(1);
});
