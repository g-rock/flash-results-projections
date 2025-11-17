import { defineStore } from 'pinia'
import { collection, doc, getDocs, collectionGroup } from 'firebase/firestore'
import { db } from '../firebase'

export const useConfigStore = defineStore('config', {
  state: () => ({
    meets: [],
    loadingMeets: false,
    meetsError: null,
    selectedGender: 'women',
    eventsData: [],
    columnDefs: [],
    loadingEvents: false,
    eventsError: null,
    selectedYear: new Date().getFullYear().toString(),
    eventStatusKeys: ['scored', 'official', 'in-progress', 'projection']
  }),

  actions: {
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
    // Fetch events for meet + gender
    // ---------------------------
    async fetchEvents(meetDocumentId) {
      if (!this.selectedGender) return

      console.log('Fetching events')
      const meet = this.meets.find(m => m.path === `meets/${meetDocumentId}`);
      if (!meet) {
        console.warn('Meet not found for documentId:', meetDocumentId)
        return
      }

      const { year, season, id } = meet
      this.loadingEvents = true
      this.eventsError = null
      this.eventsData = []
      this.columnDefs = []

      try {
        const genderCollectionRef = collection(
          doc(db, 'meets', year, season, id),
          this.selectedGender
        )

        const snapshot = await getDocs(genderCollectionRef)
        this.eventsData = snapshot.docs.map(doc => ({
          id: doc.id,
          ...doc.data(),
        }))

        const defaultColumns = [
          {
            headerName: 'Rank',
            field: 'rank',
            pinned: 'left',
            width: 70,
            valueGetter: params => params.node.rowIndex + 1,
            sortable: false,
          },
          { headerName: 'Team', field: 'team', pinned: 'left', width: 150, sortable: false },
          { 
            headerName: 'Points',
            field: 'points',
            pinned: 'left',
            sort: 'desc',
            width: 100,
            valueGetter: params => {
              let total = 0
              for (const [key, value] of Object.entries(params.data)) {
                const colDef = params?.api?.getColumnDef(key)
                if (colDef?.meta?.isEventColumn) {
                  const val = parseFloat(value)
                  if (!isNaN(val)) total += val
                }
              }
              return total
            },
          }
        ]

        const eventIndicator = {
          'projection': '🔵',
          'in-progress': '🔴',
          'official': '🟢',
          'scored': '🟢'
        }

        const eventColumns = this.eventsData.map(event => {
          const statusKey = this.eventStatusKeys.find(key => key in event)

          return {
            headerName: `${event.event_name} ${eventIndicator[statusKey] || ''}`,
            field: event.id,
            meta: { isEventColumn: true },
          }
        })

        this.columnDefs = [...defaultColumns, ...eventColumns]
      } catch (err) {
        console.error('Failed to fetch events:', err)
        this.eventsError = err.message
      } finally {
        this.loadingEvents = false
      }
    }
  },

  getters: {
    getMeetById: (state) => (id) => {
      return state.meets.find(meet => meet.id === id)
    },
    gridRowData: (state) => {
      const teamMap = {}
      const allEventIds = state.eventsData.map(e => e.id)

      state.eventsData.forEach(event => {
        const eventId = event.id
        const statusKey = state.eventStatusKeys.find(key => key in event)
        if (!statusKey) return
        
        event[statusKey]['event_results'].forEach(p => {
          const team = p.team_name
          const score = p.score || 0
          if (!teamMap[team]) teamMap[team] = { team: team }
          teamMap[team][eventId] = (teamMap[team][eventId] || 0) + score
        })
      })

      Object.values(teamMap).forEach(team => {
        allEventIds.forEach(eventId => {
          if (team[eventId] === undefined) team[eventId] = 0
        })
      })

      return Object.values(teamMap)
    }
  }
})
