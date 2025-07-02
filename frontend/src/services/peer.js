import Peer from 'peerjs';

let peer = null;
let myPeerId = null;

const initializePeer = (username) => {
  if (peer && !peer.destroyed) {
    console.warn("Peer connection already exists. Destroying old one.");
    peer.destroy();
  }
  
  myPeerId = username; // Use username as the Peer ID
  peer = new Peer(myPeerId, {
    // For now, we use the public PeerJS server.
    // In a production environment, you should host your own PeerServer.
    host: '0.peerjs.com',
    port: 443,
    path: '/',
    secure: true,
    debug: 2 // Set debug level to see detailed logs
  });

  peer.on('open', (id) => {
    console.log('PeerJS connection established. My peer ID is: ' + id);
  });

  peer.on('error', (err) => {
    console.error('PeerJS error:', err);
  });

  peer.on('disconnected', () => {
    console.log('PeerJS disconnected. PeerJS will attempt to reconnect automatically.');
  });
  
  return peer;
};

const getPeer = () => peer;
const getPeerId = () => myPeerId;

const destroyPeer = () => {
  if (peer) {
    peer.destroy();
    peer = null;
    myPeerId = null;
    console.log('PeerJS connection destroyed.');
  }
};

export { initializePeer, getPeer, getPeerId, destroyPeer }; 