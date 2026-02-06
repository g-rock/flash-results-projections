import { defineStore } from 'pinia'
import { toRaw } from 'vue'
import { collection, doc, getDocs, collectionGroup, updateDoc } from 'firebase/firestore'
import eventMap from '@/event_map.json'
import { db } from '../firebase'

const getEventResults = (event) => {
  const rawEvent = { ...toRaw(event) }
  const status = rawEvent.status

  console.log(status)

  if (
    status === 'scored' ||
    status === 'scored-protest' ||
    status === 'scored-under-review'
  ) {
    return rawEvent.scored?.event_results ?? []
  }

  if (
    status === 'official' ||
    status === 'complete' ||
    status === 'protest' ||
    status === 'under-review' ||
    status === 'in-progress' ||
    status === 'projected' ||
    status === 'scheduled' ||
    status === 'standings'
  ) {
    return (
      rawEvent.semifinal?.event_results ??
      rawEvent.prelim?.event_results ??
      rawEvent.projection?.event_results ??
      []
    )
  }

  return []
}

export const useConfigStore = defineStore('config', {
  state: () => ({
    meets: [],
    meetDocumentId: null,
    loadingMeets: false,
    meetsError: null,
    selectedGender: 'women',
    eventsData: { men: [], women: [] },
    columnDefs: { men: [], women: [] },
    genders: ['men', 'women'],
    loadingEvents: false,
    eventsError: null,
    selectedYear: new Date().getFullYear().toString(),
    scoringStatuses: ["scored", "scored-protest", "scored-under-review"],
    nonScoringStatuses: ["projected", "scheduled", "official", "complete", "in-progress"]
  }),

  actions: {
    setMeetDocumentId(id) {
      this.meetDocumentId = id
    },
    setSelectedGender(gender) {
      this.selectedGender = gender
    },
    setSelectedYear(year) {
      this.selectedYear = year.toString()
    },
    async fetchMeets() {
      this.loadingMeets = true;
      this.meetsError = null;
      this.meets = [];

      try {
        const seasons = ["indoor", "outdoor"];

        // Run both queries in parallel
        const snapshots = await Promise.all(
          seasons.map(season => getDocs(collectionGroup(db, season)))
        );

        // Flatten results
        const allMeets = [];
        snapshots.forEach((snapshot, index) => {
          const season = seasons[index];
          snapshot.docs.forEach(doc => {
            const pathParts = doc.ref.path.split("/"); // e.g. meets/2024/indoor/meet-id
            const year = pathParts[1];
            allMeets.push({
              id: doc.id,
              year,
              season,
              path: doc.ref.path,
              ...doc.data(),
            });
          });
        });

        this.meets = allMeets;
      } catch (error) {
        console.error("Failed to fetch meets from Firestore:", error);
        this.meetsError = error;
      } finally {
        this.loadingMeets = false;
      }
    },
    // ---------------------------
    // Fetch events for meet + both genders
    // ---------------------------
    async fetchEvents(meetDocumentId) {
      if (!meetDocumentId) return;

      console.log('Fetching events for both genders');
      const meet = this.meets.find(m => m.path === `meets/${meetDocumentId}`);
      if (!meet) {
        console.warn('Meet not found for documentId:', meetDocumentId);
        return;
      }

      const { year, season, id } = meet;
      this.loadingEvents = true;

      try {
        // --- Default columns (common to all genders) ---
        const defaultColumns = [
          { headerName: 'Rk', field: 'rank', sticky: true, meta: { fullHeaderName: 'Rank' } },
          { headerName: 'Team', field: 'logo', sticky: true, sortable: false, meta: { fullHeaderName: 'Team' } },
          { headerName: 'Pts', field: 'total_pts', sticky: true, meta: { fullHeaderName: 'Total Points' }},
        ];

        // --- Fetch events for each gender ---
        for (const gender of this.genders) {
          const genderCollectionRef = collection(
            doc(db, 'meets', year, season, id),
            gender
          );

          const snapshot = await getDocs(genderCollectionRef);

          const events = snapshot.docs.map(doc => ({
            id: doc.id,
            ...doc.data(),
          }));

          this.eventsData[gender] = events.slice().sort((a, b) => a.id - b.id);

          // Build columns for this gender
          const eventColumns = this.eventsData[gender].map(event => {
            const eventName = event.event_name

            let status = event.status

            return {
              headerName: eventMap[eventName] || eventName,
              field: event.id,
              meta: {
                fullHeaderName: eventName,
                isEventColumn: true,
                status
              }
            }
          })

          this.columnDefs[gender] = [...defaultColumns, ...eventColumns];
        }
      } catch (err) {
        console.error('Failed to fetch events:', err);
        this.eventsError = err.message;
      } finally {
        this.loadingEvents = false;
      }
    },
    async updateEventDoc(eventId, updates) {
      try {
        const response = await fetch(`${import.meta.env.VITE_API_HOST}/update_event`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            meetDocumentId: this.meetDocumentId,
            gender: this.selectedGender,
            eventId: eventId,
            updates
          })
        });

        if (!response.ok) {
          const text = await response.text();
          throw new Error(`API error: ${response.status} ${text}`);
        }
      } catch (err) {
        console.error("Failed to update event doc:", err);
      }
    },
    rankAndScoreEvent(results, ascending = true, isFinal) {
      const POINTS_SYSTEM = { 1: 10, 2: 8, 3: 6, 4: 5, 5: 4, 6: 3, 7: 2, 8: 1 }
      if (!results || results.length === 0) return []

      const sortField = isFinal ? 'seed_numeric' : 'sb_numeric'

      // Sort results
      const sortedResults = [...results].sort((a, b) => {
        if (ascending) return (a[sortField] || Infinity) - (b[sortField] || Infinity)
        else return (b[sortField] || -Infinity) - (a[sortField] || -Infinity)
      })

      // Assign places with tie handling
      let currentPlace = 1
      for (let i = 0; i < sortedResults.length; i++) {
        if (sortedResults[i][sortField] == null) {
          sortedResults[i].place = null
          sortedResults[i].score = 0
          continue
        }

        // Count ties
        let tieCount = 1
        while (
          i + tieCount < sortedResults.length &&
          sortedResults[i][sortField] === sortedResults[i + tieCount][sortField]
        ) {
          tieCount++
        }

        // Sum points for tied ranks
        let totalPoints = 0
        for (let r = currentPlace; r < currentPlace + tieCount; r++) {
          totalPoints += POINTS_SYSTEM[r] || 0
        }
        const avgPoints = totalPoints / tieCount

        // Assign to all tied athletes
        for (let j = 0; j < tieCount; j++) {
          sortedResults[i + j].place = currentPlace
          sortedResults[i + j].score = avgPoints
        }

        currentPlace += tieCount
        i += tieCount - 1
      }

      return sortedResults
    }
  },

  getters: {
    getMeetById: (state) => (id) => {
      return state.meets.find(meet => meet.id === id)
    },
    currentMeet: (state, getters) => {
      return getters.getMeetById(state.meetDocumentId)
    },
    selectedGenderTableData: (state) => {
      const teamMap = {}
      const eventsForGender = state.eventsData[state.selectedGender] || []
      const allEventIds = eventsForGender.map(e => e.id)

      eventsForGender.forEach(event => {
        const eventId = event.id
        const ascending = event.sort_ascending


        const results = getEventResults(event)
        if (!results.length) return

        const isFinal = !!event.scored

        const scoredResults = state.rankAndScoreEvent(results, ascending, isFinal)

        scoredResults.forEach(p => {
          const team = p.team_name
          const team_abbr = p.team_abbr
          const score = p.score || 0
          const athlete_name = p.athlete_name

          if (!teamMap[team]) {
            teamMap[team] = {
              team,
              team_abbr
            }
          }

          if (!teamMap[team][eventId]) {
            teamMap[team][eventId] = {
              event_pts: 0,
              scorers: []
            }
          }

          teamMap[team][eventId].event_pts += score
          teamMap[team][eventId].scorers.push({
            athlete_name,
            score
          })
        })
      })

      // Fill missing events + compute total points
      Object.values(teamMap).forEach(team => {
        allEventIds.forEach(eventId => {
          if (!team[eventId]) {
            team[eventId] = {
              event_pts: 0,
              scorers: []
            }
          }
        })

        team.total_pts = allEventIds.reduce(
          (sum, eventId) => sum + team[eventId].event_pts,
          0
        )
      })

      // Sort by total points desc
      const teamsArray = Object.values(teamMap).sort(
        (a, b) => b.total_pts - a.total_pts
      )

      // Assign ranks (simple, non-tie-aware)
      teamsArray.forEach((team, idx) => {
        team.rank = idx + 1
      })

      return teamsArray
    },
    selectedGenderEventData: (state) => {
      return state.eventsData[state.selectedGender];
    },
    selectedGenderColumnDefs: (state) => {
      return state.columnDefs[state.selectedGender];
    },
    selectedGenderEventStats: (state) => {
      const events = state.eventsData[state.selectedGender] || []

      const stats = {
        'total': events.length,
        'scored': 0,
        'scored-pending': 0,
        'in-progress': 0,
        'projected': 0,
      }

      events.forEach(event => {
        const status = event.status
        if (!status) return

        if (status === 'scored') {
          stats.scored++
        } else if (status === 'scored-under-review' || status === 'scored-protest') {
          stats['scored-pending']++
        } else if (status === 'in-progress') {
          stats['in-progress']++
        } else if (
          status === 'projected' ||
          status === 'scheduled' ||
          status === 'official' ||
          status === 'complete'
        ) {
          stats.projected++
        }
      })

      return stats
    }
  }
})
