import { defineStore } from 'pinia'
import { collection, doc, getDocs } from 'firebase/firestore'
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
  }),

  actions: {
    setSelectedGender(gender) {
      this.selectedGender = gender
    },
    async fetchMeets() {
      this.loadingMeets = true
      this.meetsError = null

      try {
        const meetsCollection = collection(db, 'meets')
        const snapshot = await getDocs(meetsCollection)
        this.meets = snapshot.docs.map(doc => ({
          id: doc.id,
          ...doc.data()
        }))
      } catch (error) {
        console.error('Failed to fetch meets from Firestore:', error)
        this.meetsError = error
      } finally {
        this.loadingMeets = false
      }
    },

    async fetchEvents(meetId) {
      console.log('fetching events')
      if (!meetId || !this.selectedGender) return

      this.loadingEvents = true
      this.eventsError = null
      this.eventsData = []
      this.columnDefs = []

      try {
        const genderCollectionRef = collection(
          doc(db, 'meets', meetId),
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
          { headerName: 'School', field: 'school', pinned: 'left', width: 80, sortable: false, },
          { 
            headerName: 'Points', 
            field: 'points', 
            pinned: 'left', 
            sort: 'desc',
            width: 100,
            valueGetter: params => {
              let total = 0
              for (const [key, value] of Object.entries(params.data)) {
                // Only sum fields that are marked as event scores
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
          'projections': '🔵',
          'prelims': '🟣',
          'semis': '🟡',
          'final': '🟢'
        }
        
        const eventColumns = this.eventsData.map(event => {
          const eventStatusKeys = ['final', 'semis', 'prelims', 'projections']
          const statusKey = eventStatusKeys.find(key => key in event);

          return {
            headerName: `${event.event_name} ${eventIndicator[statusKey]}`,
            field: event.id,
            meta: { 
              isEventColumn: true
            }
          };
        });

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
      const eventStatusKeys = ['final', 'semis', 'prelims', 'projections']

      state.eventsData.forEach(event => {
        const eventId = event.id
        // Pick the most “important” status that exists
        const statusKey = eventStatusKeys.find(key => key in event)
        if (!statusKey) return

        event[statusKey].forEach(p => {
          const team = p.team_abbr
          const score = p.score || 0
          if (!teamMap[team]) teamMap[team] = { school: team }
          teamMap[team][eventId] = (teamMap[team][eventId] || 0) + score
        })
      })

      // Fill in missing events with 0
      Object.values(teamMap).forEach(team => {
        allEventIds.forEach(eventId => {
          if (team[eventId] === undefined) {
            team[eventId] = 0
          }
        })
      })

      return Object.values(teamMap)
    }
  }
})
