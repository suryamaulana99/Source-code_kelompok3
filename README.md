---
title: Tubes Surya

---

# Implementasi dan Analisis Kinerja Jaringan Software Defined Network (SDN) Berbasis Topologi Spine-Leaf Menggunakan Ryu Controller dengan ECMP Load Balancing dan Firewall

---

## 1. Pendahuluan

Software Defined Network (SDN) adalah sebuah paradigma jaringan yang memisahkan *control plane* dari *data plane*, sehingga pengelolaan jaringan menjadi lebih fleksibel dan terpusat. Pada arsitektur konvensional, setiap perangkat jaringan memiliki kecerdasan sendiri untuk menentukan jalur paket. Sebaliknya, pada SDN, seluruh keputusan routing dan pengaturan trafik dilakukan oleh sebuah entitas terpusat yang disebut **controller**, sementara perangkat jaringan (switch/router) hanya bertugas meneruskan paket sesuai instruksi controller.

Implementasi SDN dilakukan menggunakan **Mininet** sebagai *network emulator*, **Ryu** sebagai *SDN controller*, dan topologi **Spine-Leaf** yang banyak digunakan pada infrastruktur *data center* modern. Selain itu, diterapkan fitur manajemen jaringan berupa **ECMP Load Balancing**, **ARP Proxy**, dan **Firewall** berbasis flow rule OpenFlow 1.3.

---

## 2. Tujuan

1. Mengimplementasikan jaringan Software Defined Networking (SDN) menggunakan Ryu Controller.
2. Merancang dan mensimulasikan topologi Spine-Leaf pada Mininet menggunakan script Python.
3. Mengimplementasikan routing berbasis SDN menggunakan protokol OpenFlow 1.3.
4. Mengimplementasikan load balancing menggunakan metode Equal Cost Multi Path (ECMP).
5. Mengimplementasikan ARP Proxy untuk mencegah ARP broadcast flooding.
6. Mengimplementasikan firewall untuk mengontrol akses komunikasi antar host.
7. Melakukan pengujian Quality of Service (QoS) meliputi throughput, delay, jitter, dan packet loss.

---

## 3. Dasar Teori

### 3.1 Software Defined Networking (SDN)

Software Defined Networking (SDN) merupakan arsitektur jaringan yang memisahkan dua fungsi utama perangkat jaringan:

- **Control Plane**: Bagian yang membuat keputusan tentang ke mana paket harus dikirim. Pada SDN, fungsi ini dipindahkan ke controller terpusat.
- **Data Plane**: Bagian yang melaksanakan keputusan tersebut, yaitu meneruskan paket berdasarkan instruksi dari controller.

Dengan pemisahan ini, administrator jaringan dapat mengelola seluruh infrastruktur dari satu titik kendali, memudahkan konfigurasi, monitoring, dan optimasi trafik secara dinamis.

**Komponen utama arsitektur SDN:**

| Komponen | Fungsi |
|---|---|
| SDN Controller | Otak jaringan; menentukan jalur paket dan kebijakan jaringan |
| OpenFlow Switch | Perangkat data plane; meneruskan paket sesuai flow table |
| Northbound API | Antarmuka antara controller dengan aplikasi jaringan |
| Southbound API | Antarmuka antara controller dengan switch (OpenFlow) |

### 3.2 OpenFlow

OpenFlow adalah protokol komunikasi standar antara SDN controller dan switch. Protokol ini memungkinkan controller memasang, memodifikasi, dan menghapus *flow rule* pada switch secara remote.

Setiap flow rule terdiri dari:
- **Match fields**: Kriteria paket yang akan dicocokkan (IP sumber/tujuan, port, MAC, dsb.)
- **Actions**: Tindakan yang dilakukan jika paket cocok (forward ke port tertentu, drop, dsb.)
- **Priority**: Urutan pengecekan jika ada beberapa rule yang cocok
- **Counters**: Statistik jumlah paket/byte yang cocok dengan rule tersebut

Pada praktikum ini digunakan **OpenFlow versi 1.3**, yang mendukung fitur seperti *multiple flow tables*, *group tables* untuk multipath, dan statistik yang lebih lengkap.

### 3.3 Ryu Controller

Ryu adalah *framework* controller SDN berbasis Python yang bersifat *open-source* dan mendukung protokol OpenFlow 1.0 hingga 1.5. Ryu menyediakan komponen-komponen siap pakai seperti:

- **Event handler**: Menangani event dari switch (PacketIn, SwitchFeatures, dsb.)
- **Packet library**: Parsing dan pembuatan paket Ethernet, ARP, IPv4, TCP, UDP, ICMP
- **Flow manager**: Instalasi dan penghapusan flow rule pada switch

Pada praktikum ini, Ryu digunakan untuk mengimplementasikan:
- Proactive routing berbasis path yang telah dihitung
- ECMP load balancing dengan metode round-robin per flow
- ARP Proxy untuk menghindari ARP flooding
- Firewall berbasis flow rule

### 3.4 Topologi Spine-Leaf

Topologi Spine-Leaf merupakan arsitektur jaringan dua lapisan (*two-tier*) yang dirancang untuk memenuhi kebutuhan *data center* modern dengan karakteristik trafik *east-west* (antar server) yang tinggi.

**Struktur topologi:**
- **Spine Switch**: Switch lapisan atas yang berfungsi sebagai *backbone*. Setiap spine terhubung ke seluruh leaf.
- **Leaf Switch**: Switch lapisan bawah yang terhubung langsung ke host/server. Setiap leaf terhubung ke seluruh spine.

**Keunggulan Spine-Leaf dibanding topologi konvensional:**

| Aspek | Topologi Konvensional (Tree) | Spine-Leaf |
|---|---|---|
| Jalur komunikasi | Single path | Multi path (jumlah spine) |
| Redundansi | Rendah | Tinggi |
| Latency | Tidak konsisten | Konsisten (maks. 2 hop) |
| Skalabilitas | Terbatas | Mudah ditambah leaf/spine |
| Bottleneck | Ada di core | Terdistribusi |

Pada implementasi ini digunakan **2 Spine** dan **4 Leaf**, sehingga setiap host memiliki **2 jalur** untuk berkomunikasi dengan host lain yang berada di leaf berbeda. Kondisi ini ideal untuk implementasi ECMP load balancing.

### 3.5 ECMP (Equal Cost Multi Path) Load Balancing

ECMP adalah metode distribusi trafik yang memanfaatkan beberapa jalur dengan biaya (*cost*) yang sama secara bersamaan. Pada topologi Spine-Leaf dengan 2 spine, setiap pasangan komunikasi antar leaf memiliki 2 jalur:

```
Host A (Leaf1) → Spine1 → Host B (Leaf2)
Host A (Leaf1) → Spine2 → Host B (Leaf2)
```

Pada implementasi ini, pemilihan spine dilakukan dengan metode **round-robin per flow**: setiap pasangan host baru mendapatkan spine yang berbeda secara bergantian. Pendekatan *per-flow* (bukan *per-packet*) dipilih untuk menghindari *packet reordering* yang dapat menurunkan performa TCP.

### 3.6 ARP Proxy

Pada jaringan konvensional, ARP (*Address Resolution Protocol*) bekerja dengan cara mem-*broadcast* request ke seluruh jaringan untuk mengetahui MAC address dari suatu IP. Pada jaringan SDN dengan banyak host, ARP broadcast dapat menyebabkan **broadcast storm** yang membebani jaringan.

ARP Proxy pada Ryu mengatasi masalah ini dengan cara: controller menyimpan tabel pemetaan IP-MAC semua host, kemudian menjawab ARP request secara langsung tanpa meneruskan broadcast ke seluruh jaringan.

### 3.7 Firewall pada SDN

Firewall pada SDN diimplementasikan melalui flow rule dengan aksi **drop** yang dipasang oleh controller. Berbeda dengan firewall konvensional yang berupa perangkat terpisah, firewall SDN bersifat *terdistribusi* dan dapat diterapkan pada switch mana pun di jaringan.

Mekanisme pada praktikum ini:
1. Saat paket pertama dari traffic yang dilarang tiba di controller (via PacketIn)
2. Controller mencocokkan dengan daftar aturan firewall
3. Jika cocok, controller memasang flow rule DROP pada switch source leaf
4. Paket pertama dibuang; paket selanjutnya langsung di-drop di switch tanpa perlu ke controller

---

## 4. Environment & Pre-Requisite

### 4.1 Hardware
- Laptop/PC dengan RAM minimal 4 GB (disarankan 8 GB untuk menjalankan 2 VM)

### 4.2 Software

| Software | Versi | Fungsi |
|---|---|---|
| VirtualBox | Terbaru | Virtualisasi VM |
| Ubuntu | 22.04 LTS | OS untuk VM Mininet dan Ryu |
| Python | 3.7 | Runtime Ryu Controller |
| Mininet | 2.3.0 | Network emulator |
| Ryu Controller | 4.34 | SDN Controller |
| iperf3 | Terbaru | Pengujian QoS |
| Wireshark | Terbaru | Analisis paket jaringan |

### 4.3 Arsitektur VM

Pada praktikum ini digunakan **2 Virtual Machine** yang terpisah:

```
┌─────────────────────────────────────────────────────┐
│                    Host Machine                     │
│                                                     │
│  ┌──────────────────┐      ┌──────────────────────┐ │
│  │   VM 1: Mininet  │      │   VM 2: Ryu          │ │
│  │  192.168.157.x   │◄────►│  192.168.157.5       │ │
│  │                  │      │                      │ │
│  │  - Mininet       │      │  - Python 3.7 venv   │ │
│  │  - OVS Switch    │      │  - Ryu Controller    │ │
│  └──────────────────┘      └──────────────────────┘ │
│           Host-Only Network (192.168.157.0/24)      │
└─────────────────────────────────────────────────────┘
```

Pemisahan ini mengikuti prinsip arsitektur SDN di mana *control plane* (Ryu) dan *data plane* (Mininet + OVS) berjalan pada node terpisah, sekaligus mensimulasikan kondisi nyata di mana controller adalah entitas terpusat yang mengelola switch secara remote.

---

## 5. Instalasi Pre-Requisite

> **Catatan**
>
> Bagian ini fokus pada instalasi **Mininet** dan **Ryu Controller**.
> Instalasi VirtualBox, Ubuntu, dan Wireshark diasumsikan telah dilakukan sebelumnya.

---

### 5.1 Instalasi Mininet

Instalasi dilakukan menggunakan metode *native installation* dari source code pada **VM 1**. Metode ini direkomendasikan karena memberikan fleksibilitas penuh dalam pengelolaan environment dan memungkinkan modifikasi langsung pada source code jika diperlukan.

**Langkah instalasi:**

**1. Install Git**
```bash
sudo apt install git
```

**2. Clone repository Mininet**
```bash
git clone https://github.com/mininet/mininet
```

**3. Masuk ke direktori Mininet**
```bash
cd mininet
```

**4. Cek versi yang tersedia**
```bash
git tag
```

**5. Pilih versi 2.3.0**
```bash
git checkout -b mininet-2.3.0 2.3.0
```

**6. Kembali ke direktori sebelumnya**
```bash
cd ..
```

**7. Jalankan instalasi lengkap**
```bash
mininet/util/install.sh -a
```

Opsi `-a` akan menginstall:
- Mininet core
- Open vSwitch (OVS)
- OpenFlow tools
- Wireshark dissector

**8. Verifikasi instalasi**
```bash
sudo mn
```

Jika berhasil, terminal akan menampilkan CLI Mininet dengan prompt `mininet>`.
<div style="text-align:center;">
    <img src="https://hackmd.io/_uploads/HkBi8UyWMl.png">
    <br>
  <em>Gambar 5.1. Tampilan Mininet setelah berhasil dijalankan</em>
</div>


---

### 5.2 Instalasi Ryu Controller

Instalasi Ryu dilakukan pada **VM 2** yang terpisah dari Mininet. Ryu dijalankan di dalam *virtual environment* Python 3.7 untuk mengisolasi dependencies.

**Langkah instalasi:**

**1. Update package list**
```bash
sudo apt update
```

**2. Tambahkan repository deadsnakes (untuk Python 3.7)**
```bash
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
```

**3. Install Python 3.7**
```bash
sudo apt install python3.7 python3.7-venv python3.7-dev
```

> Ryu memerlukan Python 3.7 karena beberapa dependensinya belum kompatibel dengan versi Python yang lebih baru.

**4. Buat virtual environment**
```bash
python3.7 -m venv ryu_venv
```

**5. Aktifkan virtual environment**
```bash
source ryu_venv/bin/activate
```

Jika berhasil, prompt terminal akan berubah menjadi `(ryu_venv) user@host:~$`.

<div style="text-align:center;">
  <img src="https://hackmd.io/_uploads/rJW8OL1WMe.png">
  <br>
  <em>Gambar 5.2. Virtual environment berhasil diaktifkan</em>
</div>

**6. Clone repository Ryu**
```bash
git clone git://github.com/osrg/ryu.git
```

**7. Pastikan folder `ryu` sudah berhasil terunduh dengan menjalankan:**
    ```bash
    ls
    ```
    Jika proses clone berhasil, maka akan muncul folder bernama **ryu** seperti pada gambar berikut:

<div style="text-align:center;">
  <img src="https://hackmd.io/_uploads/SyVGtUk-Gl.png">
  <br>
  <em>Gambar 5.4. Folder ryu berhasil terunduh</em>
</div>

**8. Masuk ke direktori Ryu dan install**
```bash
cd ryu/
pip install .
```

**9. Verifikasi instalasi**
```bash
ryu-manager --version
```

Jika versi Ryu tampil di terminal, instalasi berhasil.

<div style="text-align:center;">
  <img src="https://hackmd.io/_uploads/B1TAtIkZGe.png">
  <br>
  <em>Gambar 5.5. Verifikasi instalasi Ryu Controller berhasil</em>
</div>

> **Referensi**
> - https://mininet.org/download/
> - https://ryu-sdn.org/

---

## 6. Rancangan Topologi Jaringan

### 6.1 Gambaran Topologi

Topologi yang digunakan adalah **Spine-Leaf** dengan konfigurasi sebagai berikut:

<div style="text-align: center;">
  <img src="https://hackmd.io/_uploads/HyWtkx_bze.png">
  <em>Gambar 6.1. Topologi Jaringan Spine-Leaf</em>
</div>

### 6.2 Spesifikasi Node

| Node | DPID / IP | MAC Address | Terhubung ke |
|---|---|---|---|
| Spine S1 | 0000000000000001 | - | S3(p1), S4(p2), S5(p3), S6(p4) |
| Spine S2 | 0000000000000002 | - | S3(p1), S4(p2), S5(p3), S6(p4) |
| Leaf S3 | 0000000000000003 | - | h1(p1), h2(p2), S1(p3), S2(p4) |
| Leaf S4 | 0000000000000004 | - | h3(p1), h4(p2), S1(p3), S2(p4) |
| Leaf S5 | 0000000000000005 | - | h5(p1), h6(p2), S1(p3), S2(p4) |
| Leaf S6 | 0000000000000006 | - | h7(p1), h8(p2), S1(p3), S2(p4) |
| h1 | 192.168.10.11/24 | 00:00:10:01:00:11 | S3 port 1 |
| h2 | 192.168.10.12/24 | 00:00:10:01:00:12 | S3 port 2 |
| h3 | 192.168.10.21/24 | 00:00:10:02:00:21 | S4 port 1 |
| h4 | 192.168.10.22/24 | 00:00:10:02:00:22 | S4 port 2 |
| h5 | 192.168.10.31/24 | 00:00:10:03:00:31 | S5 port 1 |
| h6 | 192.168.10.32/24 | 00:00:10:03:00:32 | S5 port 2 |
| h7 | 192.168.10.41/24 | 00:00:10:04:00:41 | S6 port 1 |
| h8 | 192.168.10.42/24 | 00:00:10:04:00:42 | S6 port 2 |

### 6.3 Parameter Link

| Jenis Link | Bandwidth | Delay |
|---|---|---|
| Host ↔ Leaf | 10 Mbps | 1 ms |
| Leaf ↔ Spine | 10 Mbps | 2 ms |

### 6.4 Alasan Pemilihan Topologi

Topologi Spine-Leaf dipilih karena beberapa alasan:

1. **Multipath**: Dengan 2 spine, setiap pasangan host lintas leaf memiliki 2 jalur. Hal ini memungkinkan implementasi ECMP load balancing yang nyata dan terukur.
2. **Latency konsisten**: Setiap komunikasi antar leaf selalu melalui tepat 2 hop (leaf → spine → leaf), sehingga latency lebih mudah diprediksi dan dianalisis.
3. **Relevansi**: Spine-Leaf adalah arsitektur standar data center modern, sehingga relevan dengan penerapan SDN di dunia nyata.
4. **Skalabilitas**: Mudah ditambah leaf baru tanpa mengubah konfigurasi yang sudah ada.
5. **Cocok untuk fitur SDN**: Multipath yang tersedia mempermudah demonstrasi load balancing, sementara segmentasi leaf mempermudah implementasi kebijakan firewall per grup host.

---

## 7. Implementasi

### 7.1 Script Topologi Mininet

**1. Buat direktori project**
```bash
mkdir sdn-spineleaf/
cd sdn-spineleaf/
```

**2. Buat file topologi**
```bash
touch spineleaf_topology.py
nano spineleaf_topology.py
```

**3. Masukkan script berikut**

```python
from mininet.net import Mininet
from mininet.node import RemoteController, OVSKernelSwitch
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel

def build():

    net = Mininet(
        controller=RemoteController,
        switch=OVSKernelSwitch,
        link=TCLink,
        autoSetMacs=False,
        autoStaticArp=False
    )

    print("*** Adding Controller")
    c0 = net.addController(
        'c0',
        controller=RemoteController,
        ip='<IP VM yang menjalankan RYU>',
        port=6653
    )

    print("*** Adding Spine Switches")
    s1 = net.addSwitch('s1', dpid='0000000000000001', protocols='OpenFlow13')
    s2 = net.addSwitch('s2', dpid='0000000000000002', protocols='OpenFlow13')

    print("*** Adding Leaf Switches")
    s3 = net.addSwitch('s3', dpid='0000000000000003', protocols='OpenFlow13')
    s4 = net.addSwitch('s4', dpid='0000000000000004', protocols='OpenFlow13')
    s5 = net.addSwitch('s5', dpid='0000000000000005', protocols='OpenFlow13')
    s6 = net.addSwitch('s6', dpid='0000000000000006', protocols='OpenFlow13')

    print("*** Adding Hosts")
    h1 = net.addHost('h1', ip='192.168.10.11/24', mac='00:00:10:01:00:11')
    h2 = net.addHost('h2', ip='192.168.10.12/24', mac='00:00:10:01:00:12')
    h3 = net.addHost('h3', ip='192.168.10.21/24', mac='00:00:10:02:00:21')
    h4 = net.addHost('h4', ip='192.168.10.22/24', mac='00:00:10:02:00:22')
    h5 = net.addHost('h5', ip='192.168.10.31/24', mac='00:00:10:03:00:31')
    h6 = net.addHost('h6', ip='192.168.10.32/24', mac='00:00:10:03:00:32')
    h7 = net.addHost('h7', ip='192.168.10.41/24', mac='00:00:10:04:00:41')
    h8 = net.addHost('h8', ip='192.168.10.42/24', mac='00:00:10:04:00:42')

    print("*** Creating Link Parameters")
    host_link = dict(bw=10, delay='1ms', use_htb=True)
    spine_link = dict(bw=10, delay='2ms', use_htb=True)

    print("*** Connecting Hosts to Leaf Switches")
    net.addLink(h1, s3, port2=1, **host_link)
    net.addLink(h2, s3, port2=2, **host_link)
    net.addLink(h3, s4, port2=1, **host_link)
    net.addLink(h4, s4, port2=2, **host_link)
    net.addLink(h5, s5, port2=1, **host_link)
    net.addLink(h6, s5, port2=2, **host_link)
    net.addLink(h7, s6, port2=1, **host_link)
    net.addLink(h8, s6, port2=2, **host_link)

    print("*** Connecting Leaf to Spine")
    net.addLink(s3, s1, port1=3, port2=1, **spine_link)
    net.addLink(s3, s2, port1=4, port2=1, **spine_link)
    net.addLink(s4, s1, port1=3, port2=2, **spine_link)
    net.addLink(s4, s2, port1=4, port2=2, **spine_link)
    net.addLink(s5, s1, port1=3, port2=3, **spine_link)
    net.addLink(s5, s2, port1=4, port2=3, **spine_link)
    net.addLink(s6, s1, port1=3, port2=4, **spine_link)
    net.addLink(s6, s2, port1=4, port2=4, **spine_link)

    print("*** Starting Network")
    net.start()

    print("\n========== TOPOLOGY INFORMATION ==========")
    print("Controller : c0 (192.168.157.5:6653)")
    print("Spine      : s1, s2")
    print("Leaf       : s3, s4, s5, s6")
    print("------------------------------------------")
    print("h1 : 192.168.10.11  |  h2 : 192.168.10.12")
    print("h3 : 192.168.10.21  |  h4 : 192.168.10.22")
    print("h5 : 192.168.10.31  |  h6 : 192.168.10.32")
    print("h7 : 192.168.10.41  |  h8 : 192.168.10.42")
    print("==========================================\n")

    CLI(net)

    print("*** Stopping Network")
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    build()
```

**4. Simpan file** dengan `CTRL+X` → `Y` → `ENTER`

---

### 7.2 Script Ryu Controller

Script ini mengimplementasikan lima fitur utama: **ARP Proxy**, **ECMP Load Balancing**, **Proactive Routing**, **Firewall**, dan **Packet-Out Forwarding**.

**1. Buat file controller**
```bash
touch ryu_spineleaf.py
nano ryu_spineleaf.py
```

**2. Masukkan script berikut**

```python
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, arp, ipv4, tcp, udp, icmp, ether_types


class SpineLeafPolicy13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    # Tabel host: IP -> {name, mac, leaf_dpid, port_di_leaf}
    HOSTS = {
        "192.168.10.11": {"name": "h1", "mac": "00:00:10:01:00:11", "leaf": 3, "port": 1},
        "192.168.10.12": {"name": "h2", "mac": "00:00:10:01:00:12", "leaf": 3, "port": 2},
        "192.168.10.21": {"name": "h3", "mac": "00:00:10:02:00:21", "leaf": 4, "port": 1},
        "192.168.10.22": {"name": "h4", "mac": "00:00:10:02:00:22", "leaf": 4, "port": 2},
        "192.168.10.31": {"name": "h5", "mac": "00:00:10:03:00:31", "leaf": 5, "port": 1},
        "192.168.10.32": {"name": "h6", "mac": "00:00:10:03:00:32", "leaf": 5, "port": 2},
        "192.168.10.41": {"name": "h7", "mac": "00:00:10:04:00:41", "leaf": 6, "port": 1},
        "192.168.10.42": {"name": "h8", "mac": "00:00:10:04:00:42", "leaf": 6, "port": 2},
    }

    # Role setiap switch
    ROLE = {1: "spine", 2: "spine", 3: "leaf", 4: "leaf", 5: "leaf", 6: "leaf"}

    # Port di leaf yang menuju ke host
    LEAF_TO_HOST_PORT = {
        3: {"192.168.10.11": 1, "192.168.10.12": 2},
        4: {"192.168.10.21": 1, "192.168.10.22": 2},
        5: {"192.168.10.31": 1, "192.168.10.32": 2},
        6: {"192.168.10.41": 1, "192.168.10.42": 2},
    }

    # Port di leaf yang menuju ke spine
    LEAF_TO_SPINE_PORT = {
        3: {1: 3, 2: 4},
        4: {1: 3, 2: 4},
        5: {1: 3, 2: 4},
        6: {1: 3, 2: 4},
    }

    # Port di spine yang menuju ke leaf
    SPINE_TO_LEAF_PORT = {
        1: {3: 1, 4: 2, 5: 3, 6: 4},
        2: {3: 1, 4: 2, 5: 3, 6: 4},
    }

    # Aturan firewall: h4 <-> h8 diblokir di port 5001 (TCP & UDP)
    FIREWALL_RULES = [
        {"src": "192.168.10.22", "dst": "192.168.10.42", "proto": "tcp", "tp_dst": 5001},
        {"src": "192.168.10.22", "dst": "192.168.10.42", "proto": "udp", "tp_dst": 5001},
        {"src": "192.168.10.42", "dst": "192.168.10.22", "proto": "tcp", "tp_dst": 5001},
        {"src": "192.168.10.42", "dst": "192.168.10.22", "proto": "udp", "tp_dst": 5001},
    ]

    def __init__(self, *args, **kwargs):
        super(SpineLeafPolicy13, self).__init__(*args, **kwargs)
        self.datapaths = {}
        self.flow_to_spine = {}
        self.rr_index = 0

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        self.datapaths[datapath.id] = datapath
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto

        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions, idle_timeout=0, hard_timeout=0)

        role = "SPINE" if datapath.id in (1, 2) else "LEAF"
        self.logger.info("[+] Switch connected: s%d [%s]", datapath.id, role)

    def add_flow(self, datapath, priority, match, actions, idle_timeout=300, hard_timeout=0):
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(
            datapath=datapath, priority=priority, match=match,
            instructions=inst, idle_timeout=idle_timeout, hard_timeout=hard_timeout
        )
        datapath.send_msg(mod)

    def add_drop_flow(self, datapath, priority, match, idle_timeout=300, hard_timeout=0):
        parser = datapath.ofproto_parser
        mod = parser.OFPFlowMod(
            datapath=datapath, priority=priority, match=match,
            instructions=[], idle_timeout=idle_timeout, hard_timeout=hard_timeout
        )
        datapath.send_msg(mod)

    def send_packet_out(self, datapath, in_port, out_port, data, buffer_id):
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto
        actions = [parser.OFPActionOutput(out_port)]
        if buffer_id != ofproto.OFP_NO_BUFFER:
            out = parser.OFPPacketOut(
                datapath=datapath, buffer_id=buffer_id,
                in_port=in_port, actions=actions, data=None
            )
        else:
            out = parser.OFPPacketOut(
                datapath=datapath, buffer_id=ofproto.OFP_NO_BUFFER,
                in_port=in_port, actions=actions, data=data
            )
        datapath.send_msg(out)

    def _select_spine(self, src_ip, dst_ip):
        key = tuple(sorted([src_ip, dst_ip]))
        if key not in self.flow_to_spine:
            self.flow_to_spine[key] = 1 if (self.rr_index % 2 == 0) else 2
            self.rr_index += 1
            self.logger.info("[ECMP] New flow %s<->%s -> Spine%d",
                             src_ip, dst_ip, self.flow_to_spine[key])
        return self.flow_to_spine[key]

    def _path_for(self, src_ip, dst_ip):
        src_leaf = self.HOSTS[src_ip]["leaf"]
        dst_leaf = self.HOSTS[dst_ip]["leaf"]
        if src_leaf == dst_leaf:
            return [src_leaf]
        spine = self._select_spine(src_ip, dst_ip)
        return [src_leaf, spine, dst_leaf]

    def _in_port_for_segment(self, path, idx, src_ip):
        dpid = path[idx]
        if len(path) == 1:
            return self.LEAF_TO_HOST_PORT[dpid][src_ip]
        if self.ROLE[dpid] == "leaf":
            if idx == 0:
                return self.LEAF_TO_HOST_PORT[dpid][src_ip]
            else:
                spine_id = path[idx - 1]
                return self.LEAF_TO_SPINE_PORT[dpid][spine_id]
        prev_leaf = path[idx - 1]
        return self.SPINE_TO_LEAF_PORT[dpid][prev_leaf]

    def _out_port_for_segment(self, path, idx, dst_ip):
        dpid = path[idx]
        if len(path) == 1:
            return self.LEAF_TO_HOST_PORT[dpid][dst_ip]
        if self.ROLE[dpid] == "leaf":
            if idx == 0:
                next_spine = path[idx + 1]
                return self.LEAF_TO_SPINE_PORT[dpid][next_spine]
            else:
                return self.LEAF_TO_HOST_PORT[dpid][dst_ip]
        next_leaf = path[idx + 1]
        return self.SPINE_TO_LEAF_PORT[dpid][next_leaf]

    def _proxy_arp_reply(self, datapath, in_port, src_mac, src_ip, dst_mac, dst_ip, buffer_id):
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto
        pkt = packet.Packet()
        pkt.add_protocol(ethernet.ethernet(
            ethertype=ether_types.ETH_TYPE_ARP, src=dst_mac, dst=src_mac))
        pkt.add_protocol(arp.arp(
            opcode=arp.ARP_REPLY,
            src_mac=dst_mac, src_ip=dst_ip,
            dst_mac=src_mac, dst_ip=src_ip))
        pkt.serialize()
        actions = [parser.OFPActionOutput(in_port)]
        if buffer_id != ofproto.OFP_NO_BUFFER:
            out = parser.OFPPacketOut(
                datapath=datapath, buffer_id=buffer_id,
                in_port=ofproto.OFPP_CONTROLLER, actions=actions, data=None)
        else:
            out = parser.OFPPacketOut(
                datapath=datapath, buffer_id=ofproto.OFP_NO_BUFFER,
                in_port=ofproto.OFPP_CONTROLLER, actions=actions, data=pkt.data)
        datapath.send_msg(out)

    def _firewall_match(self, src_ip, dst_ip, pkt):
        tcp_seg  = pkt.get_protocol(tcp.tcp)
        udp_seg  = pkt.get_protocol(udp.udp)
        icmp_seg = pkt.get_protocol(icmp.icmp)
        if tcp_seg:
            proto, tp_dst = "tcp", tcp_seg.dst_port
        elif udp_seg:
            proto, tp_dst = "udp", udp_seg.dst_port
        elif icmp_seg:
            proto, tp_dst = "icmp", None
        else:
            return None
        for rule in self.FIREWALL_RULES:
            if rule["src"] != src_ip or rule["dst"] != dst_ip:
                continue
            if rule["proto"] != proto:
                continue
            if "tp_dst" in rule and tp_dst != rule["tp_dst"]:
                continue
            return rule
        return None

    def _install_firewall_drop(self, src_ip, dst_ip, rule):
        src_leaf = self.HOSTS[src_ip]["leaf"]
        dp = self.datapaths.get(src_leaf)
        if dp is None:
            return
        parser = dp.ofproto_parser
        match_kwargs = {
            "eth_type": ether_types.ETH_TYPE_IP,
            "ipv4_src": src_ip, "ipv4_dst": dst_ip,
        }
        if rule["proto"] == "tcp":
            match_kwargs["ip_proto"] = 6
            match_kwargs["tcp_dst"]  = rule["tp_dst"]
        elif rule["proto"] == "udp":
            match_kwargs["ip_proto"] = 17
            match_kwargs["udp_dst"]  = rule["tp_dst"]
        elif rule["proto"] == "icmp":
            match_kwargs["ip_proto"] = 1
        match = parser.OFPMatch(**match_kwargs)
        self.add_drop_flow(dp, priority=250, match=match, idle_timeout=0)
        self.logger.warning("[FIREWALL] DROP: %s -> %s (%s port=%s)",
                            src_ip, dst_ip, rule["proto"], rule.get("tp_dst", "*"))

    def _install_route(self, src_ip, dst_ip):
        for src, dst in [(src_ip, dst_ip), (dst_ip, src_ip)]:
            path = self._path_for(src, dst)
            for idx, dpid in enumerate(path):
                dp = self.datapaths.get(dpid)
                if dp is None:
                    continue
                parser   = dp.ofproto_parser
                in_port  = self._in_port_for_segment(path, idx, src)
                out_port = self._out_port_for_segment(path, idx, dst)
                match = parser.OFPMatch(
                    eth_type=ether_types.ETH_TYPE_IP,
                    ipv4_src=src, ipv4_dst=dst, in_port=in_port)
                actions = [parser.OFPActionOutput(out_port)]
                self.add_flow(dp, priority=100, match=match, actions=actions)
        self.logger.info("[ROUTE] %s <-> %s | path=%s",
                         src_ip, dst_ip, self._path_for(src_ip, dst_ip))

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg      = ev.msg
        datapath = msg.datapath
        dpid     = datapath.id
        in_port  = msg.match["in_port"]

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)
        if eth is None:
            return
        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return

        arp_pkt = pkt.get_protocol(arp.arp)
        if arp_pkt:
            if arp_pkt.opcode == arp.ARP_REQUEST and arp_pkt.dst_ip in self.HOSTS:
                dst_info = self.HOSTS[arp_pkt.dst_ip]
                self._proxy_arp_reply(
                    datapath=datapath, in_port=in_port,
                    src_mac=eth.src, src_ip=arp_pkt.src_ip,
                    dst_mac=dst_info["mac"], dst_ip=arp_pkt.dst_ip,
                    buffer_id=msg.buffer_id)
                self.logger.info("[ARP PROXY] %s -> %s replied with %s",
                                 arp_pkt.src_ip, arp_pkt.dst_ip, dst_info["mac"])
            return

        ip_pkt = pkt.get_protocol(ipv4.ipv4)
        if ip_pkt is None:
            return

        src_ip = ip_pkt.src
        dst_ip = ip_pkt.dst
        if src_ip not in self.HOSTS or dst_ip not in self.HOSTS:
            return

        rule = self._firewall_match(src_ip, dst_ip, pkt)
        if rule:
            self._install_firewall_drop(src_ip, dst_ip, rule)
            return

        self._install_route(src_ip, dst_ip)

        path = self._path_for(src_ip, dst_ip)
        if dpid not in path:
            return
        idx      = path.index(dpid)
        out_port = self._out_port_for_segment(path, idx, dst_ip)
        self.send_packet_out(datapath, in_port, out_port, msg.data, msg.buffer_id)
```

**3. Simpan file** dengan `CTRL+X` → `Y` → `ENTER`

---

## 8. Menjalankan Simulasi

### 8.1 Menjalankan Ryu Controller (VM 1)

**1. Aktifkan virtual environment**
```bash
source ryu_venv/bin/activate
```

**2. Masuk ke direktori project**
```bash
cd sdn-spineleaf/
```

**3. Jalankan Ryu Controller**
```bash
ryu-manager ryu_spineleaf.py
```

Jika berhasil, terminal akan menampilkan log seperti:
```
loading app ryu_spineleaf.py
loading app ryu.controller.ofp_handler
instantiating app ryu_spineleaf.py of SpineLeafPolicy13
```

Controller sekarang menunggu koneksi dari switch Mininet.

---

### 8.2 Menjalankan Topologi Mininet (VM 2)

**1. Masuk ke direktori project**
```bash
cd sdn-spineleaf/
```

**2. Jalankan topologi**
```bash
sudo python3 spineleaf_topology.py
```

Mininet dijalankan menggunakan script Python API karena memberikan fleksibilitas lebih tinggi dibanding `mn --custom`: konfigurasi IP, MAC, parameter QoS link, dan integrasi controller dapat dilakukan sepenuhnya dalam satu file.

Jika berhasil terhubung ke controller, log di terminal Ryu akan menampilkan:
<div style="text-align:center;">
  <img src="https://hackmd.io/_uploads/S1JoMwkZGl.png">
  <br>
  <em>Gambar 8.2. Mininet berhasil dijalankan</em>
</div>

---

### 8.3 Verifikasi Konektivitas

Sebelum pengujian QoS, lakukan verifikasi bahwa jaringan berjalan dengan benar.

**1. Test konektivitas semua host**
```bash
mininet> pingall
```

Semua host harus dapat saling berkomunikasi kecuali h4 ↔ h8 pada port yang diblokir firewall.

**2. Cek flow rule yang terpasang di spine**
```bash
mininet> sh ovs-ofctl dump-flows s1 -O OpenFlow13
mininet> sh ovs-ofctl dump-flows s2 -O OpenFlow13
```

**3. Cek flow rule di leaf**
```bash
mininet> sh ovs-ofctl dump-flows s3 -O OpenFlow13
```

**4. Cek topologi dan link**
```bash
mininet> net
mininet> links
```

---

## 9. Skenario Pengujian dan Perhitungan QoS

Pengujian dilakukan dengan 4 skenario untuk menganalisis pengaruh jumlah client dan jenis protokol terhadap parameter QoS.

### 9.1 Throughput

### Skenario S1 — Baseline (1 Client TCP)

Pada skenario ini hanya terdapat satu client yang melakukan komunikasi TCP menuju server. Skenario ini digunakan sebagai baseline untuk mengetahui performa jaringan tanpa adanya kompetisi bandwidth dari client lain.

```bash
# Terminal h1 sebagai server
mininet> h1 iperf3 -s -p 5001 &

# h5 sebagai client, durasi 30 detik, interval laporan 1 detik
mininet> h5 iperf3 -c 192.168.10.11 -p 5001 -t 30 -i 1
```

**Hasil dengan 1 client:**

<div style="text-align:center;">
  <img src="https://hackmd.io/_uploads/SkygYtbbMe.png">
  <br>
  <em>Gambar 9.1 Hasil Throughput Skenario 1 Client</em>
</div>

| Parameter | Nilai |
|------------|---------|
| Client | h5 → h1 |
| Jumlah Client | 1 |
| Throughput Sender | 12.5 Mbps |
| Throughput Receiver | 9.53 Mbps |
| Retransmission | 0 |

### Analisis

Berdasarkan hasil pengujian, throughput yang diterima server mencapai **9.53 Mbps** dengan throughput pengirim sebesar **12.5 Mbps**. Tidak ditemukan retransmission selama proses komunikasi sehingga jaringan dapat bekerja secara optimal tanpa adanya kompetisi bandwidth.

---

### Skenario S2 — Multi Client (3 Client TCP Serentak)
Pada skenario ini host **h1** berperan sebagai server, sedangkan host **h3**, **h5**, dan **h7** berperan sebagai client yang mengirimkan trafik TCP secara bersamaan menuju server h1 melalui port yang berbeda.

#### Pada xterm h1

```bash
iperf3 -s -p 5001 &
iperf3 -s -p 5002 &
iperf3 -s -p 5003 &
```

#### Pada xterm h3

```bash
iperf3 -c 192.168.10.11 -p 5001 -t 30 -i 1
```

#### Pada xterm h5

```bash
iperf3 -c 192.168.10.11 -p 5002 -t 30 -i 1
```

#### Pada xterm h7

```bash
iperf3 -c 192.168.10.11 -p 5003 -t 30 -i 1
```

**Hasil dengan 3 Client:**
<div style="text-align:center;">
  <img src="https://hackmd.io/_uploads/rkg0huZZzl.png">
  <br>
  <em>Gambar 9.2 Hasil Throughput Skenario 3 Client</em>
</div>

Pada skenario ini tiga client (h3, h5, dan h7) secara bersamaan mengirimkan trafik TCP menuju server h1. Pengujian dilakukan untuk melihat pengaruh peningkatan beban jaringan terhadap throughput yang diperoleh.

| Client | Throughput Sender | Throughput Receiver | Retransmission |
|----------|------------------|---------------------|----------------|
| h3 → h1 | 12.0 Mbps | 8.99 Mbps | 0 |
| h5 → h1 | 6.86 Mbps | 5.79 Mbps | 83 |
| h7 → h1 | 12.3 Mbps | 9.50 Mbps | 0 |

---

## Tabel Perbandingan Hasil Pengujian Throughput

| Parameter | Skenario 1 (1 Client) | Skenario 2 (3 Client) |
|------------|---------------|---------------|
| Jumlah Client | 1 | 3 |
| Throughput Rata-rata Sender | 12.5 Mbps | 10.39 Mbps |
| Throughput Rata-rata Receiver | 9.53 Mbps | 8.09 Mbps |
| Retransmission | 0 | 83 |
| Beban Jaringan | Rendah | Tinggi |
| Kompetisi Bandwidth | Tidak Ada | Ada |

---

### Analisis Hasil

Berdasarkan hasil pengujian, Skenario 1 menghasilkan throughput receiver sebesar **9.53 Mbps** tanpa retransmission karena hanya terdapat satu client yang menggunakan jaringan. Kondisi ini menunjukkan bahwa bandwidth dapat dimanfaatkan secara optimal tanpa adanya kompetisi trafik.

Pada Skenario 2, tiga client melakukan transmisi TCP secara bersamaan menuju server yang sama. Akibatnya terjadi kompetisi bandwidth pada jalur jaringan sehingga throughput rata-rata receiver menurun menjadi **8.09 Mbps**. Selain itu ditemukan **83 retransmission** pada client h5 yang mengindikasikan adanya congestion atau antrian paket selama proses pengiriman data.

Secara keseluruhan, peningkatan jumlah client menyebabkan penurunan throughput sekitar **15%**, dari **9.53 Mbps** pada Skenario 1 menjadi **8.09 Mbps** pada Skenario 2. Hasil ini menunjukkan bahwa semakin besar beban trafik yang diberikan, maka performa jaringan akan mengalami penurunan meskipun komunikasi antar host masih dapat berjalan dengan baik.

---

### 9.2 Delay

Pengukuran delay dilakukan menggunakan protokol **ICMP** melalui perintah `ping` sebanyak 50 paket. Nilai delay yang dilaporkan adalah **one-way delay**, yaitu setengah dari nilai RTT (*Round Trip Time*) rata-rata.

```bash
mininet> h5 ping -c 50 192.168.10.11
```
Hasil:
<div style="text-align:center;">
  <img src="https://hackmd.io/_uploads/HJqDXTbWMx.png">
  <br>
  <em>Gambar 9.2 Hasil Pengujian Delay Menggunakan Ping</em>
</div>

### Hasil Pengujian Delay

Pengujian delay dilakukan menggunakan perintah ping sebanyak 50 paket dari host sumber menuju host tujuan.

Hasil pengujian:

| Parameter | Nilai |
|------------|---------|
| Minimum Delay | 13.285 ms |
| Average Delay (RTT) | 16.239 ms |
| Maximum Delay | 52.858 ms |
| Mdev | 5.319 ms |

### Perhitungan Delay

Delay satu arah (*one-way delay*) dapat diestimasi menggunakan setengah dari nilai RTT rata-rata.

$$
Delay = \frac{RTT}{2}
$$

$$
Delay = \frac{16.239}{2}
$$

$$
Delay = 8.12 \ ms
$$

### Analisis

Berdasarkan hasil pengujian, diperoleh nilai RTT rata-rata sebesar **16.239 ms**. Jika diasumsikan waktu tempuh paket dari pengirim ke penerima bersifat simetris, maka diperoleh estimasi delay satu arah sebesar **8.12 ms**. Nilai ini menunjukkan bahwa jaringan memiliki waktu respons yang relatif rendah sehingga komunikasi antar host dapat berlangsung dengan baik.

---

## 9.3 Jitter

### Skenario Pengujian

Server dijalankan pada host h1 dan client dijalankan pada host h5 menggunakan protokol UDP dengan bandwidth 5 Mbps selama 30 detik.

```bash
mininet> h1 iperf3 -s -p 5001 &
mininet> h5 iperf3 -c 192.168.10.11 -u -b 5M -p 5001 -t 30 -i 1
```

### Hasil Pengujian

<div style="text-align:center;">
  <img src="https://hackmd.io/_uploads/H10coR-Wfg.png">
  <br>
  <em>Gambar 9.3 hasil pengujian UDP</em>
</div>

Dari hasil pengujian diperoleh nilai jitter sebagai berikut:

| Parameter | Nilai |
|------------|---------|
| Jitter | 1.022 ms |

### Analisis

Nilai jitter yang diperoleh sebesar **1.022 ms**. Nilai ini menunjukkan variasi waktu kedatangan paket yang sangat kecil sehingga aliran data berlangsung dengan stabil. Semakin kecil nilai jitter, semakin baik kualitas layanan jaringan karena paket diterima dengan interval waktu yang lebih konsisten.

---

## 9.4 Packet Loss

### Skenario Pengujian

Pengujian packet loss dilakukan menggunakan skenario UDP yang sama dengan pengujian jitter.

```bash
mininet> h1 iperf3 -s -p 5001 &
mininet> h5 iperf3 -c 192.168.10.11 -u -b 5M -p 5001 -t 30 -i 1
```

### Hasil Pengujian

Dari hasil pengujian diperoleh:

<div style="text-align:center;">
  <img src="https://hackmd.io/_uploads/H10coR-Wfg.png">
  <br>
  <em>Gambar 9.4 hasil pengujian UDP</em>
</div>

| Parameter | Nilai |
|------------|---------|
| Total Datagram | 12949 |
| Paket Hilang | 0 |
| Packet Loss | 0% |

### Perhitungan Packet Loss

$$
Packet\ Loss = \frac{Paket\ Hilang}{Total\ Paket} \times 100\%
$$

$$
Packet\ Loss = \frac{0}{12949} \times 100\%
$$

$$
Packet\ Loss = 0\%
$$

### Analisis

Hasil pengujian menunjukkan bahwa tidak terdapat paket yang hilang selama proses transmisi berlangsung. Nilai **packet loss sebesar 0%** menandakan bahwa seluruh paket UDP berhasil diterima oleh host tujuan sehingga reliabilitas jaringan dapat dikatakan sangat baik.

---

### 9.5 Verifikasi Firewall

Pengujian firewall dilakukan untuk membuktikan bahwa Ryu Controller berhasil memblokir komunikasi antara **h4 (192.168.10.22)** dan **h8 (192.168.10.42)** pada port **5001** menggunakan mekanisme flow rule OpenFlow 1.3.

---

### Cara Kerja Firewall pada SDN

Firewall pada implementasi ini bekerja secara *reactive*, yaitu:

1. Paket pertama dari h4 ke h8 port 5001 masuk ke controller via **PacketIn**
2. Controller mencocokkan paket dengan `FIREWALL_RULES`
3. Jika cocok, controller memasang **flow rule DROP** di switch S4 (switch yang terhubung langsung ke h4)
4. Seluruh paket selanjutnya langsung di-drop di S4 **tanpa perlu ke controller**

Pendekatan ini lebih efisien dibanding firewall konvensional karena pemblokiran terjadi di switch terdekat dengan sumber traffic.

---
Langkah Pengujian
1. Jalankan server iperf3 di h8

```bash
# h8 sebagai server di port 5001
mininet> h8 iperf3 -s -p 5001 &

# h4 mencoba konek ke h8 port 5001 — HARUS GAGAL
mininet> h4 iperf3 -c 192.168.10.42 -p 5001 -t 10

#Lakukan cek terhadap flow table
mininet> sh ovs-ofctl dump-flows s4 -O OpenFlow13
```
<div style="text-align:center;">
  <img src="https://hackmd.io/_uploads/SJkdS8f-Mx.png">
  <br>
  <em>Gambar 9.5 Hasil pengujian firewall</em>
</div>

2. Verifikasi ping h4 ke h8
```
# Verifikasi h4 MASIH bisa ping h8 (ICMP tidak diblokir)
mininet> h4 ping -c 5 192.168.10.42
```
<div style="text-align:center;">
  <img src="https://hackmd.io/_uploads/r1ZjYIfbMg.png">
  <br>
  <em>Gambar 9.5 Hasil ping h4 ke h8</em>
</div>

3. Verifikasi port lain yang tidak di blokir firewall
```
# Verifikasi port lain TIDAK diblokir
mininet> h4 iperf3 -c 192.168.10.42 -p 9999 -t 10
```
<div style="text-align:center;">
  <img src="https://hackmd.io/_uploads/SJAq_UM-Gx.png">
  <br>
  <em>Gambar 9.5 Verifikasi port 9999</em>
</div>

**4. Cek flow rule yang terpasang di switch S4**
```bash
mininet> sh ovs-ofctl dump-flows s4 -O OpenFlow13
```
<div style="text-align:center;">
  <img src="https://hackmd.io/_uploads/r128Jwfbzl.png">
  <br>
  <em>Gambar 9.5 Flow rule s4</em>
</div>

---

### Tabel Hasil Verifikasi Firewall

| Pengujian | Hasil yang Diharapkan | Hasil Aktual | Status |
| --- | --- | --- | --- |
| h4 → h8 port 5001 TCP | BLOCKED | Bad file descriptor | ✅ BLOCKED |
| h4 → h8 ICMP (ping) | ALLOWED | 5/5 paket berhasil | ✅ ALLOWED |
| h4 → h8 port 9999 TCP | ALLOWED | 11.7 Mbits/sec | ✅ ALLOWED |
| Flow rule DROP di S4 | actions=drop | priority=250 actions=drop | ✅ TERPASANG |
| Paket yang di-drop | n_packets > 0 | n_packets=21 | ✅ 21 paket di-drop |

### Analisis Firewall

1. **Flow rule DROP berhasil terpasang di S4** dengan prioritas 250, lebih tinggi dari rule forward biasa (prioritas 100), sehingga traffic h4 → h8 port 5001 selalu dicocokkan dengan rule DROP terlebih dahulu sebelum rule lainnya.

2. **Error "Bad file descriptor" pada iperf3** bukan error koneksi biasa, melainkan indikasi bahwa paket TCP dari h4 di-drop di switch S4 sebelum sempat mencapai h8. Berbeda dengan "Connection refused" yang berarti paket sampai ke tujuan namun ditolak aplikasi, pada kasus ini h4 tidak pernah mendapat balasan apapun karena paket dibuang di level switch.

3. **Ping (ICMP) tetap berhasil** karena aturan firewall hanya memblokir protokol TCP dan UDP pada port 5001. Hal ini membuktikan bahwa firewall bersifat selektif dan tidak mempengaruhi jenis komunikasi lain antara h4 dan h8.

4. **Port 9999 berhasil terkoneksi** dengan throughput 11.7 Mbits/sec dan tanpa retransmisi (Retr=0). Ini membuktikan bahwa firewall hanya memblokir port yang telah dikonfigurasi (port 5001) tanpa mempengaruhi komunikasi pada port lain antara h4 dan h8.

5. **Pemblokiran terjadi di switch terdekat (S4)** yaitu switch yang terhubung langsung ke h4 sebagai sumber traffic. Pendekatan ini lebih efisien karena paket dibuang sedini mungkin tanpa perlu diteruskan ke switch lain, sehingga tidak membebani bandwidth jaringan secara keseluruhan.

6. **n_packets=21** pada flow rule DROP menunjukkan bahwa selama seluruh sesi pengujian terdapat 21 paket dari h4 yang berhasil diblokir oleh firewall, membuktikan mekanisme drop berjalan secara konsisten meskipun ada traffic port lain yang tetap diizinkan.
---

### 9.6 Verifikasi ECMP Load Balancing

Equal Cost Multi Path (ECMP) merupakan metode load balancing yang memungkinkan beberapa jalur dengan cost yang sama digunakan secara bersamaan untuk mengirimkan trafik. Pada topologi Spine-Leaf, setiap leaf switch memiliki lebih dari satu jalur menuju tujuan melalui spine switch yang berbeda.

Pada implementasi ini, controller Ryu menerapkan mekanisme ECMP berbasis flow menggunakan metode round-robin. Setiap flow baru akan diarahkan ke salah satu spine switch secara bergantian sehingga beban trafik tidak terpusat pada satu jalur saja.

---

### Skenario Pengujian

Pengujian dilakukan dengan mengirimkan trafik TCP secara bersamaan dari tiga client menuju server h1.

```bash
mininet> h1 iperf3 -s -p 5001 &
mininet> h1 iperf3 -s -p 5002 &
mininet> h1 iperf3 -s -p 5003 &

mininet> sh sleep 3

mininet> h3 iperf3 -c 192.168.10.11 -p 5001 -t 30 &
mininet> h5 iperf3 -c 192.168.10.11 -p 5002 -t 30 &
mininet> h7 iperf3 -c 192.168.10.11 -p 5003 -t 30 &

mininet> sh sleep 5
```

Selanjutnya dilakukan pengecekan jalur yang dipilih oleh controller dan flow yang terpasang pada masing-masing spine switch.

```bash
# Cek counter flow pada spine switch
mininet> sh ovs-ofctl dump-flows s1 -O OpenFlow13 | grep n_packets
mininet> sh ovs-ofctl dump-flows s2 -O OpenFlow13 | grep n_packets
```

---

### Hasil Pengujian

Log pada controller menunjukkan bahwa flow berhasil didistribusikan ke beberapa jalur spine menggunakan mekanisme ECMP berbasis round-robin.

<div style="text-align:center;">
  <img src="https://hackmd.io/_uploads/ryRNiPz-Ge.png">
  <br>
  <em>Gambar 9.6 Log ECMP pada controller</em>
</div>

Counter flow pada switch spine menunjukkan paket diteruskan melalui kedua jalur yang tersedia.

<div style="text-align:center;">
  <img src="https://hackmd.io/_uploads/r1VD2vfWze.png">
  <br>
  <em>Gambar 9.7 Counter flow pada spine switch</em>
</div>

Controller berhasil mendistribusikan trafik melalui dua jalur spine yang tersedia.

| Flow | Jalur |
|--------|--------|
| h3 → h1 | Spine 1 (s1) |
| h5 → h1 | Spine 2 (s2) |
| h7 → h1 | Spine 1 (s1) |

Log controller menunjukkan:

```text
[ECMP] New flow 192.168.10.21<->192.168.10.11 → Spine1
[ECMP] New flow 192.168.10.31<->192.168.10.11 → Spine2
[ECMP] New flow 192.168.10.41<->192.168.10.11 → Spine1
```

Berdasarkan hasil dump flow pada switch spine diperoleh jumlah paket sebagai berikut:

| Spine | Jumlah Paket | Persentase |
|---------|---------:|---------:|
| s1 | 16.730 | 78.82% |
| s2 | 4.496 | 21.18% |
| Total | 21.226 | 100% |

---

### Analisis

Hasil pengujian menunjukkan bahwa controller berhasil mendistribusikan flow ke lebih dari satu jalur spine menggunakan mekanisme ECMP. Flow dari h3 diarahkan melalui Spine 1, flow dari h5 melalui Spine 2, dan flow dari h7 kembali melalui Spine 1 sesuai algoritma round-robin yang diterapkan.

Distribusi trafik yang diperoleh tidak harus bernilai 50:50 karena ECMP pada implementasi ini bekerja berdasarkan flow (*per-flow load balancing*), bukan berdasarkan jumlah paket. Oleh karena itu, perbedaan jumlah paket pada masing-masing spine switch merupakan hal yang normal karena ukuran dan durasi setiap flow dapat berbeda.

Selama flow berhasil didistribusikan ke beberapa jalur yang tersedia dan tidak seluruh trafik melewati satu spine switch saja, maka mekanisme ECMP dapat dinyatakan berjalan dengan baik.

Dengan demikian, implementasi ECMP pada topologi Spine-Leaf berhasil meningkatkan pemanfaatan jalur jaringan dan mencegah seluruh trafik terkonsentrasi pada satu spine switch.

---

## 10. Kesimpulan

1. Topologi Spine-Leaf berhasil diimplementasikan pada Mininet menggunakan script Python dengan 2 spine switch, 4 leaf switch, dan 8 host.
2. Implementasi Ryu Controller berhasil menjalankan fungsi routing, ARP proxy, dan ECMP load balancing secara terpusat.
3. Mekanisme ECMP berhasil mendistribusikan flow ke dua spine switch secara round-robin sehingga beban trafik tidak hanya terpusat pada satu jalur.
4. Firewall berbasis flow rule berhasil memblokir komunikasi h4 ↔ h8 pada port 5001 tanpa mengganggu komunikasi lain seperti ping maupun port yang berbeda.
5. Hasil pengujian QoS menunjukkan bahwa throughput menurun ketika jumlah client bertambah, dengan nilai throughput receiver 9.53 Mbps pada 1 client dan 8.09 Mbps pada 3 client.
6. Pengujian delay menggunakan ICMP menghasilkan RTT rata-rata sebesar 16.239 ms atau estimasi one-way delay sebesar 8.12 ms.
7. Pengujian UDP menunjukkan nilai jitter sebesar 1.022 ms dan packet loss sebesar 0%, yang menandakan jaringan masih stabil dan tidak mengalami kehilangan paket.

Secara keseluruhan, topologi Spine-Leaf yang dikombinasikan dengan Ryu Controller terbukti cocok digunakan untuk simulasi jaringan SDN karena mendukung pengelolaan terpusat, load balancing, keamanan jaringan, serta pengukuran QoS dengan hasil yang baik.

---

## Referensi

- [Mininet Official Documentation](https://mininet.org/)
- [Ryu SDN Framework](https://ryu-sdn.org/)
- [OpenFlow 1.3 Specification](https://opennetworking.org/wp-content/uploads/2014/10/openflow-spec-v1.3.0.pdf)
- [Open vSwitch Documentation](https://docs.openvswitch.org/)