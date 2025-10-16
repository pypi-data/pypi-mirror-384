use serde::Serialize;

use crate::{
    session_stats::SessionCountersSnapshot,
    stream_connect::ConnectStatsSnapshot,
    torrent_state::{peers::stats::AggregatePeerStats, stats::Speed},
};

use super::SessionStats;

#[derive(Debug, Serialize)]
pub struct SessionStatsSnapshot {
    pub counters: SessionCountersSnapshot,
    pub download_speed: Speed,
    pub upload_speed: Speed,
    pub peers: AggregatePeerStats,
    pub uptime_seconds: u64,
    pub connections: ConnectStatsSnapshot,
}

impl From<(&SessionStats, ConnectStatsSnapshot)> for SessionStatsSnapshot {
    fn from((s, c): (&SessionStats, ConnectStatsSnapshot)) -> Self {
        Self {
            download_speed: s.down_speed_estimator.mbps().into(),
            upload_speed: s.up_speed_estimator.mbps().into(),
            counters: s.counters.snapshot(),
            peers: s.peers.snapshot(),
            uptime_seconds: s.startup_time.elapsed().as_secs(),
            connections: c,
        }
    }
}

impl SessionStatsSnapshot {
    pub fn as_prometheus(&self, mut out: &mut String) {
        use core::fmt::Write;

        out.push('\n');

        macro_rules! m {
            ($type:ident, $name:ident, $value:expr) => {{
                writeln!(
                    &mut out,
                    concat!("# TYPE ", stringify!($name), " ", stringify!($type))
                )
                .unwrap();
                writeln!(&mut out, concat!(stringify!($name), " {}"), $value).unwrap();
            }};
        }

        m!(counter, rqbit_fetched_bytes, self.counters.fetched_bytes);
        m!(counter, rqbit_uploaded_bytes, self.counters.uploaded_bytes);
        m!(
            counter,
            rqbit_blocked_incoming,
            self.counters.blocked_incoming
        );
        m!(
            counter,
            rqbit_blocked_outgoing,
            self.counters.blocked_outgoing
        );
        m!(
            gauge,
            rqbit_download_speed_bytes,
            self.download_speed.as_bytes()
        );
        m!(
            gauge,
            rqbit_upload_speed_bytes,
            self.upload_speed.as_bytes()
        );
        m!(gauge, rqbit_uptime_seconds, self.uptime_seconds);
        m!(gauge, rqbit_peers_connecting, self.peers.connecting);
        writeln!(&mut out, "# TYPE rqbit_peers_live gauge").unwrap();
        writeln!(
            &mut out,
            "rqbit_peers_live{{kind=\"tcp\"}} {}",
            self.peers.live_tcp
        )
        .unwrap();
        writeln!(
            &mut out,
            "rqbit_peers_live{{kind=\"utp\"}} {}",
            self.peers.live_utp
        )
        .unwrap();
        writeln!(
            &mut out,
            "rqbit_peers_live{{kind=\"socks\"}} {}",
            self.peers.live_socks
        )
        .unwrap();
        m!(gauge, rqbit_peers_dead, self.peers.dead);
        m!(gauge, rqbit_peers_not_needed, self.peers.not_needed);
        m!(gauge, rqbit_peers_queued, self.peers.queued);
        m!(gauge, rqbit_peers_queued, self.peers.seen);
        m!(gauge, rqbit_peers_steals, self.peers.steals);
    }
}
