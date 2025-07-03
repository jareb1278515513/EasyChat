import Peer from 'peerjs';

let peer = null;

const encodeUsernameForPeerId = (username) => {
  // Use Base64 encoding that is safe for PeerJS IDs.
  // btoa(unescape(encodeURIComponent(str))) is a common trick to handle Unicode.
  // The '=' padding is removed as it's not a valid PeerJS ID character.
  return btoa(unescape(encodeURIComponent(username))).replace(/=/g, "");
};

const decodeUsernameFromPeerId = (peerId) => {
  // Add the removed Base64 padding back before decoding.
  let paddedId = peerId;
  switch (peerId.length % 4) {
    case 2:
      paddedId += '==';
      break;
    case 3:
      paddedId += '=';
      break;
  }
  // Use the corresponding decoding trick.
  return decodeURIComponent(escape(atob(paddedId)));
};

const initializePeer = (username) => {
  if (peer && !peer.destroyed) {
    console.warn("Peer connection already exists. Destroying old one.");
    peer.destroy();
  }
  
  const peerId = encodeUsernameForPeerId(username);
  peer = new Peer(peerId, {
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

const destroyPeer = () => {
  if (peer) {
    peer.destroy();
    peer = null;
    console.log('PeerJS connection destroyed.');
  }
};

export { 
  initializePeer, 
  getPeer, 
  destroyPeer, 
  encodeUsernameForPeerId, 
  decodeUsernameFromPeerId 
}; 