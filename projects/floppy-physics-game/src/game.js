import * as THREE from 'three';
import * as CANNON from 'cannon-es';

const root = document.getElementById('game');
const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(devicePixelRatio, 1.5));
renderer.setSize(innerWidth, innerHeight);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.outputColorSpace = THREE.SRGBColorSpace;
root.appendChild(renderer.domElement);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x86b9dc);
scene.fog = new THREE.Fog(0x86b9dc, 34, 92);

const camera = new THREE.PerspectiveCamera(58, innerWidth / innerHeight, 0.08, 180);
let camYaw = 0;
let camPitch = 0.28;
let camDistance = 7.2;
const cameraTarget = new THREE.Vector3();

const hemi = new THREE.HemisphereLight(0xe9f6ff, 0x4b545b, 1.45);
scene.add(hemi);
const sun = new THREE.DirectionalLight(0xffffff, 2.25);
sun.position.set(-12, 18, 10);
sun.castShadow = true;
sun.shadow.mapSize.set(1024, 1024);
sun.shadow.camera.left = -24;
sun.shadow.camera.right = 24;
sun.shadow.camera.top = 24;
sun.shadow.camera.bottom = -24;
sun.shadow.camera.near = 0.5;
sun.shadow.camera.far = 70;
sun.shadow.bias = -0.0003;
sun.shadow.normalBias = 0.025;
scene.add(sun);
scene.add(sun.target);

// Unity-like starter floor: solid neutral plane + grid overlay.
const floorMat = new THREE.MeshStandardMaterial({ color: 0x9da3a8, roughness: 0.94, metalness: 0 });
const floorMesh = new THREE.Mesh(new THREE.PlaneGeometry(80, 80), floorMat);
floorMesh.rotation.x = -Math.PI / 2;
floorMesh.receiveShadow = true;
scene.add(floorMesh);
const grid = new THREE.GridHelper(80, 80, 0x4f5961, 0x707980);
grid.position.y = 0.006;
grid.material.opacity = 0.75;
grid.material.transparent = true;
scene.add(grid);

const world = new CANNON.World({ gravity: new CANNON.Vec3(0, -9.82, 0) });
world.allowSleep = false;
world.solver.iterations = 18;
world.solver.tolerance = 0.001;
const floorPhysMat = new CANNON.Material('floor');
const playerPhysMat = new CANNON.Material('player');
world.addContactMaterial(new CANNON.ContactMaterial(floorPhysMat, playerPhysMat, {
  friction: 0.86,
  restitution: 0.0,
  contactEquationStiffness: 1e8,
  contactEquationRelaxation: 3
}));
const floorBody = new CANNON.Body({ mass: 0, material: floorPhysMat, shape: new CANNON.Plane() });
floorBody.quaternion.setFromEuler(-Math.PI / 2, 0, 0);
floorBody.collisionFilterGroup = 1;
floorBody.collisionFilterMask = 2;
world.addBody(floorBody);

const sync = [];
const parts = {};
const playerBodies = [];
const constraints = [];

function meshMaterial(color, rough = 0.72) {
  return new THREE.MeshStandardMaterial({ color, roughness: rough, metalness: 0 });
}

function addBoxPart(name, half, position, mass, color, radiusLook = false) {
  const shape = new CANNON.Box(new CANNON.Vec3(half.x, half.y, half.z));
  const body = new CANNON.Body({ mass, material: playerPhysMat, shape, position: new CANNON.Vec3(position.x, position.y, position.z) });
  body.linearDamping = 0.12;
  body.angularDamping = 0.72;
  body.collisionFilterGroup = 2;
  body.collisionFilterMask = 1;
  world.addBody(body);
  let geo;
  if (radiusLook) {
    const r = Math.max(half.x, half.z);
    geo = new THREE.CapsuleGeometry(r, Math.max(0.02, half.y * 2 - r * 2), 5, 10);
  } else {
    geo = new THREE.BoxGeometry(half.x * 2, half.y * 2, half.z * 2, 1, 1, 1);
  }
  const mesh = new THREE.Mesh(geo, meshMaterial(color));
  mesh.castShadow = true;
  mesh.receiveShadow = true;
  scene.add(mesh);
  sync.push({ body, mesh });
  parts[name] = { body, mesh };
  playerBodies.push(body);
  return parts[name];
}

function addSpherePart(name, radius, position, mass, color) {
  const body = new CANNON.Body({ mass, material: playerPhysMat, shape: new CANNON.Sphere(radius), position: new CANNON.Vec3(position.x, position.y, position.z) });
  body.linearDamping = 0.10;
  body.angularDamping = 0.70;
  body.collisionFilterGroup = 2;
  body.collisionFilterMask = 1;
  world.addBody(body);
  const mesh = new THREE.Mesh(new THREE.SphereGeometry(radius, 18, 14), meshMaterial(color, 0.78));
  mesh.castShadow = true;
  mesh.receiveShadow = true;
  scene.add(mesh);
  sync.push({ body, mesh });
  parts[name] = { body, mesh };
  playerBodies.push(body);
  return parts[name];
}

function p2p(a, pivotA, b, pivotB, maxForce = 1e6) {
  const c = new CANNON.PointToPointConstraint(a.body, new CANNON.Vec3(...pivotA), b.body, new CANNON.Vec3(...pivotB), maxForce);
  c.collideConnected = false;
  world.addConstraint(c);
  constraints.push(c);
  return c;
}

function buildPlayer() {
  addBoxPart('pelvis', { x: 0.38, y: 0.24, z: 0.23 }, { x: 0, y: 2.42, z: 0 }, 3.4, 0x355c7d);
  addBoxPart('torso', { x: 0.48, y: 0.48, z: 0.25 }, { x: 0, y: 3.14, z: 0 }, 4.6, 0x66a6c8);
  addSpherePart('head', 0.37, { x: 0, y: 4.08, z: 0 }, 1.15, 0xf2e6d7);
  addBoxPart('upperArmL', { x: 0.18, y: 0.43, z: 0.18 }, { x: -0.71, y: 3.05, z: 0 }, 0.75, 0xf2e6d7, true);
  addBoxPart('lowerArmL', { x: 0.16, y: 0.41, z: 0.16 }, { x: -0.71, y: 2.22, z: 0 }, 0.58, 0xf2e6d7, true);
  addBoxPart('upperArmR', { x: 0.18, y: 0.43, z: 0.18 }, { x: 0.71, y: 3.05, z: 0 }, 0.75, 0xf2e6d7, true);
  addBoxPart('lowerArmR', { x: 0.16, y: 0.41, z: 0.16 }, { x: 0.71, y: 2.22, z: 0 }, 0.58, 0xf2e6d7, true);
  addBoxPart('upperLegL', { x: 0.22, y: 0.47, z: 0.22 }, { x: -0.25, y: 1.73, z: 0 }, 1.45, 0x29455d, true);
  addBoxPart('lowerLegL', { x: 0.19, y: 0.45, z: 0.19 }, { x: -0.25, y: 0.82, z: 0 }, 1.15, 0xf2e6d7, true);
  addBoxPart('footL', { x: 0.22, y: 0.13, z: 0.35 }, { x: -0.25, y: 0.27, z: -0.10 }, 0.55, 0x4a5157);
  addBoxPart('upperLegR', { x: 0.22, y: 0.47, z: 0.22 }, { x: 0.25, y: 1.73, z: 0 }, 1.45, 0x29455d, true);
  addBoxPart('lowerLegR', { x: 0.19, y: 0.45, z: 0.19 }, { x: 0.25, y: 0.82, z: 0 }, 1.15, 0xf2e6d7, true);
  addBoxPart('footR', { x: 0.22, y: 0.13, z: 0.35 }, { x: 0.25, y: 0.27, z: -0.10 }, 0.55, 0x4a5157);

  // Face detail gives direction without copying another game's character asset.
  const eyeGeo = new THREE.SphereGeometry(0.042, 8, 6);
  const eyeMat = new THREE.MeshBasicMaterial({ color: 0x26323a });
  const eyeL = new THREE.Mesh(eyeGeo, eyeMat);
  const eyeR = new THREE.Mesh(eyeGeo, eyeMat);
  eyeL.position.set(-0.12, 0.05, -0.34);
  eyeR.position.set(0.12, 0.05, -0.34);
  parts.head.mesh.add(eyeL, eyeR);

  // Strong core + loose limbs: active ragdoll instead of a normal animated capsule.
  const core = new CANNON.LockConstraint(parts.pelvis.body, parts.torso.body, { maxForce: 2.6e5 });
  core.collideConnected = false;
  world.addConstraint(core);
  constraints.push(core);
  p2p(parts.torso, [0, 0.48, 0], parts.head, [0, -0.36, 0]);
  p2p(parts.torso, [-0.48, 0.18, 0], parts.upperArmL, [0, 0.42, 0]);
  p2p(parts.upperArmL, [0, -0.42, 0], parts.lowerArmL, [0, 0.40, 0]);
  p2p(parts.torso, [0.48, 0.18, 0], parts.upperArmR, [0, 0.42, 0]);
  p2p(parts.upperArmR, [0, -0.42, 0], parts.lowerArmR, [0, 0.40, 0]);
  p2p(parts.pelvis, [-0.24, -0.22, 0], parts.upperLegL, [0, 0.45, 0]);
  p2p(parts.upperLegL, [0, -0.45, 0], parts.lowerLegL, [0, 0.44, 0]);
  p2p(parts.lowerLegL, [0, -0.43, 0], parts.footL, [0, 0.11, 0.18]);
  p2p(parts.pelvis, [0.24, -0.22, 0], parts.upperLegR, [0, 0.45, 0]);
  p2p(parts.upperLegR, [0, -0.45, 0], parts.lowerLegR, [0, 0.44, 0]);
  p2p(parts.lowerLegR, [0, -0.43, 0], parts.footR, [0, 0.11, 0.18]);
}

buildPlayer();

const spawn = new CANNON.Vec3(0, 2.42, 0);
const initialOffsets = {};
for (const [name, p] of Object.entries(parts)) {
  initialOffsets[name] = new CANNON.Vec3(p.body.position.x - spawn.x, p.body.position.y - spawn.y, p.body.position.z - spawn.z);
}

function resetPlayer() {
  for (const [name, p] of Object.entries(parts)) {
    const off = initialOffsets[name];
    p.body.position.set(spawn.x + off.x, spawn.y + off.y, spawn.z + off.z);
    p.body.quaternion.set(0, 0, 0, 1);
    p.body.velocity.set(0, 0, 0);
    p.body.angularVelocity.set(0, 0, 0);
    p.body.force.set(0, 0, 0);
    p.body.torque.set(0, 0, 0);
    p.body.wakeUp();
  }
}

document.getElementById('reset').addEventListener('pointerdown', e => { e.preventDefault(); resetPlayer(); });

let joyX = 0;
let joyY = 0;
let joyPointer = null;
const joy = document.getElementById('joystick');
const knob = document.getElementById('knob');
function updateJoy(e) {
  const r = joy.getBoundingClientRect();
  let dx = e.clientX - (r.left + r.width / 2);
  let dy = e.clientY - (r.top + r.height / 2);
  const max = r.width * 0.34;
  const len = Math.hypot(dx, dy) || 1;
  if (len > max) { dx *= max / len; dy *= max / len; }
  knob.style.transform = `translate(${dx}px, ${dy}px)`;
  joyX = dx / max;
  joyY = -dy / max;
}
joy.addEventListener('pointerdown', e => { e.preventDefault(); joyPointer = e.pointerId; joy.setPointerCapture(e.pointerId); updateJoy(e); });
joy.addEventListener('pointermove', e => { if (e.pointerId === joyPointer) updateJoy(e); });
function endJoy(e) {
  if (e.pointerId !== joyPointer) return;
  joyPointer = null; joyX = 0; joyY = 0; knob.style.transform = 'translate(0px, 0px)';
}
joy.addEventListener('pointerup', endJoy);
joy.addEventListener('pointercancel', endJoy);

let camPointer = null;
let camLastX = 0, camLastY = 0;
renderer.domElement.addEventListener('pointerdown', e => {
  if (e.clientX < innerWidth * 0.38 && e.clientY > innerHeight * 0.48) return;
  camPointer = e.pointerId; camLastX = e.clientX; camLastY = e.clientY;
  renderer.domElement.setPointerCapture(e.pointerId);
});
renderer.domElement.addEventListener('pointermove', e => {
  if (e.pointerId !== camPointer) return;
  const dx = e.clientX - camLastX, dy = e.clientY - camLastY;
  camLastX = e.clientX; camLastY = e.clientY;
  camYaw -= dx * 0.006;
  camPitch = THREE.MathUtils.clamp(camPitch + dy * 0.0045, -0.10, 0.82);
});
renderer.domElement.addEventListener('pointerup', e => { if (e.pointerId === camPointer) camPointer = null; });
renderer.domElement.addEventListener('pointercancel', e => { if (e.pointerId === camPointer) camPointer = null; });

let jumpQueued = false;
document.getElementById('jump').addEventListener('pointerdown', e => { e.preventDefault(); jumpQueued = true; });

const tQuat = new THREE.Quaternion();
const up = new THREE.Vector3();
const forward = new THREE.Vector3();
const worldUp = new THREE.Vector3(0, 1, 0);
const axis = new THREE.Vector3();
const desiredDir = new THREE.Vector3();
const camForward = new THREE.Vector3();
const camRight = new THREE.Vector3();
let walkClock = 0;

function applyBalance(dt) {
  const torso = parts.torso.body;
  const pelvis = parts.pelvis.body;
  tQuat.set(torso.quaternion.x, torso.quaternion.y, torso.quaternion.z, torso.quaternion.w);
  up.set(0, 1, 0).applyQuaternion(tQuat).normalize();
  axis.crossVectors(up, worldUp);
  torso.torque.x += axis.x * 72 - torso.angularVelocity.x * 5.4;
  torso.torque.z += axis.z * 72 - torso.angularVelocity.z * 5.4;
  pelvis.torque.x += axis.x * 30 - pelvis.angularVelocity.x * 2.8;
  pelvis.torque.z += axis.z * 30 - pelvis.angularVelocity.z * 2.8;

  camForward.set(-Math.sin(camYaw), 0, -Math.cos(camYaw)).normalize();
  camRight.set(Math.cos(camYaw), 0, -Math.sin(camYaw)).normalize();
  desiredDir.copy(camRight).multiplyScalar(joyX).addScaledVector(camForward, joyY);
  const mag = Math.min(1, desiredDir.length());
  if (mag > 0.04) desiredDir.normalize();

  const speed = Math.hypot(pelvis.velocity.x, pelvis.velocity.z);
  if (mag > 0.04) {
    const force = Math.max(0, 92 - speed * 12) * mag;
    pelvis.force.x += desiredDir.x * force;
    pelvis.force.z += desiredDir.z * force;
    torso.force.x += desiredDir.x * force * 0.35;
    torso.force.z += desiredDir.z * force * 0.35;

    // Face the travel direction with a soft physical torque, not an animation snap.
    forward.set(0, 0, -1).applyQuaternion(tQuat); forward.y = 0; forward.normalize();
    const crossY = forward.x * desiredDir.z - forward.z * desiredDir.x;
    const dot = THREE.MathUtils.clamp(forward.dot(desiredDir), -1, 1);
    const yawError = Math.atan2(crossY, dot);
    torso.torque.y += -yawError * 26 - torso.angularVelocity.y * 3.2;

    walkClock += dt * (5.2 + speed * 0.45);
    const step = Math.sin(walkClock);
    const leftPush = Math.max(0, step);
    const rightPush = Math.max(0, -step);
    const legForce = 16 * mag;
    parts.upperLegL.body.force.x += desiredDir.x * legForce * leftPush;
    parts.upperLegL.body.force.z += desiredDir.z * legForce * leftPush;
    parts.upperLegR.body.force.x += desiredDir.x * legForce * rightPush;
    parts.upperLegR.body.force.z += desiredDir.z * legForce * rightPush;
  }

  // Active-ragdoll height spring: enough to stand, weak enough to fall and wobble.
  const upright = THREE.MathUtils.clamp((up.y + 0.15) / 1.15, 0, 1);
  const desiredY = 2.42;
  const lift = THREE.MathUtils.clamp((desiredY - pelvis.position.y) * 68 - pelvis.velocity.y * 8, -15, 74) * (0.28 + upright * 0.72);
  pelvis.force.y += lift;

  const grounded = Math.min(parts.footL.body.position.y, parts.footR.body.position.y) < 0.58 && pelvis.position.y < 2.9;
  if (jumpQueued && grounded) {
    const impulse = new CANNON.Vec3(0, 7.0, 0);
    pelvis.applyImpulse(impulse);
    torso.applyImpulse(new CANNON.Vec3(0, 3.1, 0));
  }
  jumpQueued = false;
}

let last = performance.now() / 1000;
let accumulator = 0;
const fixed = 1 / 60;
function animate() {
  requestAnimationFrame(animate);
  const now = performance.now() / 1000;
  let dt = Math.min(0.04, now - last);
  last = now;
  accumulator += dt;
  while (accumulator >= fixed) {
    applyBalance(fixed);
    world.step(fixed);
    accumulator -= fixed;
  }

  for (const s of sync) {
    s.mesh.position.set(s.body.position.x, s.body.position.y, s.body.position.z);
    s.mesh.quaternion.set(s.body.quaternion.x, s.body.quaternion.y, s.body.quaternion.z, s.body.quaternion.w);
  }

  const torsoPos = parts.torso.body.position;
  cameraTarget.lerp(new THREE.Vector3(torsoPos.x, torsoPos.y + 0.15, torsoPos.z), 0.12);
  const cp = Math.cos(camPitch), sp = Math.sin(camPitch);
  const offset = new THREE.Vector3(Math.sin(camYaw) * cp, sp, Math.cos(camYaw) * cp).multiplyScalar(camDistance);
  camera.position.copy(cameraTarget).add(offset).add(new THREE.Vector3(0, 1.0, 0));
  camera.lookAt(cameraTarget.x, cameraTarget.y + 0.45, cameraTarget.z);
  sun.target.position.copy(cameraTarget);
  sun.target.updateMatrixWorld();

  if (parts.pelvis.body.position.y < -8 || Math.abs(parts.pelvis.body.position.x) > 45 || Math.abs(parts.pelvis.body.position.z) > 45) resetPlayer();
  renderer.render(scene, camera);
}
animate();

addEventListener('resize', () => {
  camera.aspect = innerWidth / innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
  renderer.setPixelRatio(Math.min(devicePixelRatio, 1.5));
});
