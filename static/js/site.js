// const sleep = ms => new Promise(r => setTimeout(r, ms));
// async function syncsleep(ms) {
//     await sleep(ms);
// }

document.addEventListener("DOMContentLoaded", function(event) {
    fetch('./podcasts/hansel/episodes')
        .then(response => response.json())
        .then(data => {
            let episodes = document.querySelector('#episodes');
            data.forEach(episode => {
                let a = document.createElement('a');
                a.href = "#";
                a.classList.add('list-group-item', 'list-group-item-action');
                a.innerText = `#${episode.id}: ${episode.title}`;
                a.onclick = function(e) {
                    e.preventDefault();
                    document.querySelectorAll('#episodes a').forEach(node => {
                        node.classList.remove('active');
                        node.ariaCurrent = 'false';
                    });
                    a.classList.add('active');
                    a.ariaCurrent = 'true';
                    fetch(`./podcasts/hansel/episodes/${episode.id}`)
                        .then(response => response.json())
                        .then(data => {
                            document.querySelector('#episode-summary').innerText = data.summary;
                        });
                };
                episodes.appendChild(a);
            });
            episodes.firstElementChild.click();
        });

    document.querySelectorAll('#suggestedQs a').forEach(node =>
        node.addEventListener('click', function(e) {
        let q = e.target.innerText;
        document.querySelector('#question').innerText = q;
        document.querySelector('#answer').innerText = '';
        let evtSource = new EventSource(`./ask?q=${q}`);
        evtSource.onmessage = (event) => {
            document.querySelector('#answer').innerText += event.data;
        };
        evtSource.onerror = (error) => {
            evtSource.close();
        };
    }));
});
